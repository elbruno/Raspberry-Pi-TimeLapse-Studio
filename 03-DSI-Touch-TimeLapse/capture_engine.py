"""
capture_engine.py - Background Capture Engine for Touch TimeLapse

Runs the time-lapse capture loop in a dedicated background thread.
The main (GUI) thread starts / stops capture and polls status via a
thread-safe ``get_status()`` method.

Usage:
    engine = CaptureEngine()
    engine.start(session, camera, storage, config)
    while engine.is_running:
        info = engine.get_status()
        ...
    engine.stop()
"""

import logging
import threading
import time
from datetime import datetime
from typing import Optional

from camera_opencv import OpenCVCamera
from config import get_config_value
from storage_manager import Session, StorageManager

try:
    from led_controller import LEDController
    LED_AVAILABLE = True
except ImportError:
    LED_AVAILABLE = False
    LEDController = None  # type: ignore[assignment, misc]

try:
    from grove_status_light import GroveStatusLight
    GROVE_LIGHT_AVAILABLE = True
except ImportError:
    GROVE_LIGHT_AVAILABLE = False
    GroveStatusLight = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)

MAX_RETRIES = 3          # consecutive capture failures before giving up
RETRY_DELAY_S = 1.0      # seconds between retry attempts


class CaptureEngine:
    """
    Background capture engine that photographs at a fixed interval.

    All public state is guarded by ``threading.Lock`` so it is safe to
    read from the GUI thread while the capture thread is writing.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # Shared state (access under _lock)
        self._running: bool = False
        self._total_photos: int = 0
        self._start_time: Optional[datetime] = None
        self._errors: list[str] = []
        self._last_photo_path: Optional[str] = None
        self._next_capture_mono: float = 0.0  # monotonic timestamp of next capture
        self._interval: float = 30.0

    # -- public interface -----------------------------------------------------

    def start(self, session: Session, camera: OpenCVCamera,
              storage: StorageManager, config: dict,
              led: Optional["LEDController"] = None,
              status_light: Optional["GroveStatusLight"] = None) -> None:  # type: ignore[name-defined]
        """
        Begin the capture loop in a background thread.

        Args:
            session: Active Session object (may be new or resumed).
            camera:  Already-opened OpenCVCamera.
            storage: StorageManager pointed at the session base path.
            config:  Merged configuration dictionary.
            led:     Optional LEDController for illumination before capture.
            status_light: Optional GroveStatusLight for visual app state.
        """
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Capture engine is already running")
            return

        self._stop_event.clear()

        with self._lock:
            self._running = True
            self._total_photos = session.total_photos
            self._start_time = datetime.now()
            self._errors = list(session.errors)
            self._last_photo_path = None

        self._thread = threading.Thread(
            target=self._capture_loop,
            args=(session, camera, storage, config, led, status_light),
            name="capture-engine",
            daemon=True,
        )
        self._thread.start()
        logger.info("Capture engine started for session %s", session.session_id)

    def stop(self) -> None:
        """Signal the capture loop to finish and wait for the thread."""
        self._stop_event.set()

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=10)
            if self._thread.is_alive():
                logger.warning("Capture thread did not stop within timeout")

        with self._lock:
            self._running = False
            self._next_capture_mono = 0.0

        logger.info("Capture engine stopped")

    @property
    def is_running(self) -> bool:
        """Thread-safe check if the capture loop is active."""
        with self._lock:
            return self._running

    def get_status(self) -> dict:
        """
        Return a snapshot of capture progress.

        Returns:
            Dictionary with ``total_photos``, ``elapsed_seconds``,
            ``errors``, ``last_photo_path``, and ``next_capture_in``.
        """
        with self._lock:
            elapsed = 0.0
            if self._start_time:
                elapsed = (datetime.now() - self._start_time).total_seconds()
            # Countdown to next capture (seconds remaining)
            next_in = 0.0
            if self._running and self._next_capture_mono > 0:
                next_in = max(0.0, self._next_capture_mono - time.monotonic())
            return {
                "total_photos": self._total_photos,
                "elapsed_seconds": round(elapsed, 1),
                "errors": list(self._errors),
                "last_photo_path": self._last_photo_path,
                "is_running": self._running,
                "next_capture_in": round(next_in, 0),
                "interval": self._interval,
            }

    # -- internal capture loop ------------------------------------------------

    def _capture_loop(self, session: Session, camera: OpenCVCamera,
                      storage: StorageManager, config: dict,
                      led: Optional["LEDController"] = None,
                      status_light: Optional["GroveStatusLight"] = None) -> None:  # type: ignore[name-defined]
        """Main loop executed inside the background thread."""
        interval = get_config_value(config, "capture.interval_seconds", 30)
        quality = get_config_value(config, "capture.quality", 90)
        retry_delay = get_config_value(config, "capture.retry_delay_seconds", RETRY_DELAY_S)
        consecutive_failures = 0

        # LED settings
        led_enabled = get_config_value(config, "led.enabled", True)
        led_warmup = get_config_value(config, "led.warmup_seconds", 1.0)
        use_led = led_enabled and led is not None and led.is_available()
        if use_led:
            logger.info("LED illumination enabled — warmup %.1fs", led_warmup)

        capture_flash = get_config_value(config, "grove_light.capture_flash", True)
        use_status_light = (
            capture_flash
            and status_light is not None
            and status_light.is_available()
        )
        if use_status_light:
            status_light.set_state("capturing")  # type: ignore[union-attr]
            logger.info(
                "Grove status light flash enabled — warmup %.1fs before each capture",
                led_warmup,
            )

        logger.info("Capture loop running — interval=%ss, quality=%d",
                     interval, quality)

        with self._lock:
            self._interval = float(interval)

        try:
            while not self._stop_event.is_set():
                next_capture = time.monotonic() + interval

                # Publish the next-capture timestamp for the countdown UI
                with self._lock:
                    self._next_capture_mono = next_capture

                # -- LED ON before capture --
                # Both the USB LEDController (illumination) and the Grove
                # status light (visual indicator) turn ON `led_warmup` seconds
                # before the snapshot, then OFF again after.
                if use_led:
                    led.turn_on()  # type: ignore[union-attr]
                if use_status_light:
                    # Bright white pre-flash so the user sees the snapshot moment
                    status_light.set_capture_active(True)  # type: ignore[union-attr]

                if use_led or use_status_light:
                    # Wait for warmup (interruptible)
                    warmup_end = time.monotonic() + led_warmup
                    while not self._stop_event.is_set():
                        remaining = warmup_end - time.monotonic()
                        if remaining <= 0:
                            break
                        self._stop_event.wait(timeout=min(remaining, 0.25))
                    if self._stop_event.is_set():
                        if use_led:
                            led.turn_off()  # type: ignore[union-attr]
                        if use_status_light:
                            status_light.set_state("off")  # type: ignore[union-attr]
                        break

                # -- attempt to capture a frame --
                frame = None
                for attempt in range(1, MAX_RETRIES + 1):
                    frame = camera.capture()
                    if frame is not None:
                        consecutive_failures = 0
                        break
                    logger.warning("Capture attempt %d/%d failed",
                                   attempt, MAX_RETRIES)
                    time.sleep(retry_delay)

                # -- LED stays ON briefly after capture, then OFF --
                # Wait `led_warmup` seconds with LED still on so the user sees
                # a clear "flash" duration around each snapshot.
                if use_led or use_status_light:
                    post_end = time.monotonic() + led_warmup
                    while not self._stop_event.is_set():
                        remaining = post_end - time.monotonic()
                        if remaining <= 0:
                            break
                        self._stop_event.wait(timeout=min(remaining, 0.25))

                if use_led:
                    led.turn_off()  # type: ignore[union-attr]
                if use_status_light:
                    # Return to the "capturing" steady state between shots
                    status_light.set_capture_active(False)  # type: ignore[union-attr]

                if frame is None:
                    consecutive_failures += 1
                    error_msg = (
                        f"Camera failed after {MAX_RETRIES} retries "
                        f"(consecutive: {consecutive_failures})"
                    )
                    logger.error(error_msg)
                    with self._lock:
                        self._errors.append(error_msg)
                        session.errors.append(error_msg)

                    if consecutive_failures >= MAX_RETRIES:
                        logger.error("Too many consecutive failures — stopping")
                        break
                else:
                    # -- save the photo --
                    path = storage.save_photo(session, frame, quality)
                    if path:
                        with self._lock:
                            self._total_photos = session.total_photos
                            self._last_photo_path = path
                    else:
                        error_msg = "Failed to save photo to disk"
                        logger.error(error_msg)
                        with self._lock:
                            self._errors.append(error_msg)
                            session.errors.append(error_msg)

                # Persist metadata after every capture cycle
                storage.save_session_metadata(session)

                # -- sleep until next capture, checking for stop --
                self._interruptible_sleep(next_capture)

        except Exception as e:
            logger.exception("Unhandled error in capture loop: %s", e)
            with self._lock:
                self._errors.append(f"Unexpected error: {e}")
                session.errors.append(f"Unexpected error: {e}")

        # -- finalise session --
        session.end_time = datetime.now()
        session.status = "stopped"
        storage.save_session_metadata(session)

        if use_status_light:
            status_light.set_state("stopped")  # type: ignore[union-attr]

        with self._lock:
            self._running = False

        logger.info("Capture loop finished — %d photos captured",
                     session.total_photos)

    def _interruptible_sleep(self, wake_time: float) -> None:
        """Sleep until *wake_time* (monotonic), waking early on stop signal."""
        while not self._stop_event.is_set():
            remaining = wake_time - time.monotonic()
            if remaining <= 0:
                break
            self._stop_event.wait(timeout=min(remaining, 0.25))

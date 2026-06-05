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
from typing import Callable, Optional

from camera_opencv import OpenCVCamera
from config import get_config_value
from storage_manager import Session, StorageManager

try:
    from led_controller import LEDController
    LED_AVAILABLE = True
except ImportError:
    LED_AVAILABLE = False
    LEDController = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)

MAX_RETRIES = 3          # consecutive capture failures before triggering reopen
RETRY_DELAY_S = 1.0      # seconds between retry attempts
REOPEN_BACKOFF_S = [3.0, 6.0, 12.0, 30.0]  # exponential backoff caps
STORAGE_RETRY_BACKOFF_S = [2.0, 5.0, 10.0, 30.0]  # USB drive reappear waits


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
              relay_2: Optional["LEDController"] = None,
              camera_reopen_callback: Optional[Callable[[], Optional[OpenCVCamera]]] = None) -> None:  # type: ignore[name-defined]
        """
        Begin the capture loop in a background thread.

        Args:
            session: Active Session object (may be new or resumed).
            camera:  Already-opened OpenCVCamera.
            storage: StorageManager pointed at the session base path.
            config:  Merged configuration dictionary.
            led:     Optional Relay #1 controller for illumination before capture.
            relay_2: Optional Relay #2 controller for illumination before capture.
            camera_reopen_callback: Optional callable invoked when the camera
                stops responding. Should reinitialise the device and return a
                fresh ``OpenCVCamera`` instance, or ``None`` if it is still
                unavailable. The engine retries with exponential backoff and
                does not give up until the user stops the session.
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
            args=(session, camera, storage, config, led, relay_2,
                  camera_reopen_callback),
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
                      relay_2: Optional["LEDController"] = None,
                      camera_reopen_callback: Optional[Callable[[], Optional[OpenCVCamera]]] = None) -> None:  # type: ignore[name-defined]
        """Main loop executed inside the background thread."""
        interval = get_config_value(config, "capture.interval_seconds", 30)
        quality = get_config_value(config, "capture.quality", 90)
        retry_delay = get_config_value(config, "capture.retry_delay_seconds", RETRY_DELAY_S)
        consecutive_failures = 0

        # LED settings
        led_enabled = get_config_value(config, "led.enabled", True)
        led_warmup = get_config_value(config, "led.warmup_seconds", 1.5)
        led_pre_lead = get_config_value(config, "led.pre_capture_lead_seconds", 0.0)
        # Total time LED stays on BEFORE the snapshot fires.
        led_pre_total = max(0.0, float(led_warmup) + float(led_pre_lead))
        relay_2_enabled = get_config_value(config, "grove_relay_2.enabled", True)

        active_relays: list[tuple[str, "LEDController"]] = []  # type: ignore[name-defined]
        if led_enabled and led is not None and led.is_available():
            active_relays.append(("relay_1", led))
        if relay_2_enabled and relay_2 is not None and relay_2.is_available():
            active_relays.append(("relay_2", relay_2))

        if active_relays:
            logger.info(
                "Relay illumination enabled (%d relay%s) — warmup %.1fs",
                len(active_relays),
                "s" if len(active_relays) > 1 else "",
                led_warmup,
            )

        def _set_relays(on: bool) -> None:
            action = "on" if on else "off"
            for name, controller in active_relays:
                try:
                    if on:
                        controller.turn_on()
                    else:
                        controller.turn_off()
                except Exception as exc:
                    logger.warning("Failed turning %s %s: %s", name, action, exc)

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
                # Relay/illumination turns ON before the snapshot, then OFF
                # immediately after frame capture.
                if active_relays:
                    _set_relays(on=True)

                if active_relays:
                    # Wait pre-capture lead time (warmup + extra lead, interruptible)
                    warmup_end = time.monotonic() + led_pre_total
                    while not self._stop_event.is_set():
                        remaining = warmup_end - time.monotonic()
                        if remaining <= 0:
                            break
                        self._stop_event.wait(timeout=min(remaining, 0.25))
                    if self._stop_event.is_set():
                        _set_relays(on=False)
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

                # Turn relay/LED off immediately after the frame attempt.
                if active_relays:
                    _set_relays(on=False)

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

                    # Try to reopen the camera with exponential backoff.
                    # The session keeps running until the user explicitly stops.
                    if camera_reopen_callback is not None:
                        new_cam = self._reopen_camera_with_backoff(camera_reopen_callback)
                        if new_cam is not None:
                            camera = new_cam
                            consecutive_failures = 0
                            with self._lock:
                                self._errors.append("Camera reconnected")
                                session.errors.append("Camera reconnected")
                    else:
                        # No reopen callback available — fall back to old behaviour
                        if consecutive_failures >= MAX_RETRIES:
                            logger.error("Too many consecutive failures — stopping")
                            break
                else:
                    # -- save the photo --
                    path = self._save_photo_with_retry(storage, session, frame, quality)
                    if path:
                        with self._lock:
                            self._total_photos = session.total_photos
                            self._last_photo_path = path

                # Persist metadata after every capture cycle (best-effort)
                self._save_metadata_with_retry(storage, session)

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
        self._save_metadata_with_retry(storage, session)

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

    def _reopen_camera_with_backoff(
        self,
        reopen_callback: Callable[[], Optional[OpenCVCamera]],
    ) -> Optional[OpenCVCamera]:
        """Try to reopen the camera with exponential backoff.

        Returns the new camera handle on success, or ``None`` if the user
        stopped the session before recovery succeeded. Never gives up on
        its own — only the stop_event breaks the loop.
        """
        attempt = 0
        while not self._stop_event.is_set():
            delay = REOPEN_BACKOFF_S[min(attempt, len(REOPEN_BACKOFF_S) - 1)]
            logger.info(
                "Attempting camera reopen in %.1fs (attempt #%d)",
                delay, attempt + 1,
            )
            # Wait the backoff window (interruptible)
            wake = time.monotonic() + delay
            while not self._stop_event.is_set():
                remaining = wake - time.monotonic()
                if remaining <= 0:
                    break
                self._stop_event.wait(timeout=min(remaining, 0.25))
            if self._stop_event.is_set():
                return None

            try:
                new_cam = reopen_callback()
            except Exception as exc:
                logger.warning("Camera reopen callback raised: %s", exc)
                new_cam = None

            if new_cam is not None and new_cam.is_available():
                logger.info("Camera reopened successfully")
                return new_cam

            attempt += 1
        return None

    def _save_photo_with_retry(
        self,
        storage: StorageManager,
        session: Session,
        frame,
        quality: int,
    ) -> Optional[str]:
        """Save a photo, retrying with backoff if storage is unavailable."""
        for delay in STORAGE_RETRY_BACKOFF_S:
            if self._stop_event.is_set():
                return None
            # Verify the storage base path is still mounted before writing.
            if not storage.base_path.exists():
                msg = f"Storage path missing: {storage.base_path} — waiting {delay:.1f}s"
                logger.warning(msg)
                with self._lock:
                    if not self._errors or self._errors[-1] != msg:
                        self._errors.append(msg)
                        session.errors.append(msg)
                wake = time.monotonic() + delay
                while not self._stop_event.is_set():
                    remaining = wake - time.monotonic()
                    if remaining <= 0:
                        break
                    self._stop_event.wait(timeout=min(remaining, 0.25))
                continue

            path = storage.save_photo(session, frame, quality)
            if path:
                return path

            err = "Failed to save photo to disk"
            logger.error(err)
            with self._lock:
                self._errors.append(err)
                session.errors.append(err)
            # Brief pause before retrying in case of a transient I/O hiccup
            self._stop_event.wait(timeout=delay)
        return None

    def _save_metadata_with_retry(
        self,
        storage: StorageManager,
        session: Session,
    ) -> None:
        """Persist session metadata; tolerate transient storage outages."""
        try:
            if not storage.base_path.exists():
                # Skip silently — _save_photo_with_retry already logged it.
                return
            storage.save_session_metadata(session)
        except Exception as exc:
            logger.warning("Could not save session metadata: %s", exc)

#!/usr/bin/env python3
"""
PiTimeLapse Touch — Graphical timelapse capture app for Raspberry Pi touchscreens.

Main entry point.  Wires together the camera, capture engine, storage, USB
detection, and pygame UI into a single event-loop application.

Designed for 480×320 Pi touchscreen (Waveshare / Kuman) but also runs
windowed on any desktop for development and testing.

Usage:
    python timelapse_touch.py              # windowed (desktop)
    python timelapse_touch.py --fullscreen # fullscreen (Pi LCD)
"""

from __future__ import annotations

import logging
import os
import platform
import signal
import sys
import threading
import time
import glob
from typing import Optional

# ---------------------------------------------------------------------------
# SDL environment — must be set BEFORE importing pygame.
# When running via SSH while a desktop session is active on the LCD,
# we inject DISPLAY=:0 so SDL uses X11.  If no desktop is running we
# fall back to kmsdrm / fbcon / directfb.  "dummy" is never used — it
# renders to nothing.
# ---------------------------------------------------------------------------
_SDL_NEEDS_PROBE = False
if platform.system() == "Linux" and not os.environ.get("DISPLAY"):
    # Check whether an X server is running on :0 (desktop on the LCD).
    # This is the typical case when running via SSH while the Pi desktop
    # is displayed on the touchscreen.
    _x_running = os.path.exists("/tmp/.X11-unix/X0")
    if _x_running:
        os.environ["DISPLAY"] = ":0"
        # Some setups also need XAUTHORITY so X11 accepts the connection
        if not os.environ.get("XAUTHORITY"):
            _xa = os.path.expanduser("~/.Xauthority")
            if os.path.exists(_xa):
                os.environ["XAUTHORITY"] = _xa
        logging.getLogger(__name__).info("No DISPLAY set — using :0 (desktop detected)")
    else:
        # True headless / console — target framebuffer
        os.environ.setdefault("SDL_FBDEV", "/dev/fb0")
        os.environ.setdefault("SDL_MOUSEDEV", "/dev/input/touchscreen")
        os.environ.setdefault("SDL_MOUSEDRV", "TSLIB")
        _SDL_NEEDS_PROBE = True

import numpy as np
import pygame


def _init_display_driver() -> None:
    """Initialise the SDL video driver.

    If DISPLAY is set (local or injected above) pygame auto-detects fine.
    Otherwise probe kmsdrm → fbcon → directfb one at a time.
    """
    if not _SDL_NEEDS_PROBE:
        pygame.display.init()
        return

    drivers = ["kmsdrm", "fbcon", "directfb"]
    for driver in drivers:
        os.environ["SDL_VIDEODRIVER"] = driver
        try:
            pygame.display.init()
            logging.getLogger(__name__).info("SDL video driver: %s", driver)
            return
        except pygame.error:
            pygame.display.quit()

    # Last resort — let SDL choose (may still fail)
    os.environ.pop("SDL_VIDEODRIVER", None)
    pygame.display.init()

# Local UI components
from ui_components import (
    Button,
    Header,
    PreviewArea,
    SettingsScreen,
    StatusBar,
    ThumbnailArea,
    COLOR_BACKGROUND,
    COLOR_CLOSE,
    COLOR_SETTINGS,
    COLOR_START,
    COLOR_STOP,
    COLOR_TEXT,
)

# Backend modules (built by Linguini in parallel — import defensively)
try:
    from camera_opencv import OpenCVCamera
    CAMERA_AVAILABLE = True
except ImportError:
    CAMERA_AVAILABLE = False
    OpenCVCamera = None  # type: ignore[assignment, misc]

try:
    from capture_engine import CaptureEngine
    CAPTURE_ENGINE_AVAILABLE = True
except ImportError:
    CAPTURE_ENGINE_AVAILABLE = False
    CaptureEngine = None  # type: ignore[assignment, misc]

try:
    from storage_manager import StorageManager
    STORAGE_AVAILABLE = True
except ImportError:
    STORAGE_AVAILABLE = False
    StorageManager = None  # type: ignore[assignment, misc]

try:
    from usb_detector import find_first_usb_drive, get_drive_info
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False

try:
    from config import load_config, save_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

try:
    from led_controller import LEDController
    LED_MODULE_AVAILABLE = True
except ImportError:
    LED_MODULE_AVAILABLE = False
    LEDController = None  # type: ignore[assignment, misc]

try:
    from grove_dual_button import GroveDualButton
    GROVE_BUTTON_AVAILABLE = True
except ImportError:
    GROVE_BUTTON_AVAILABLE = False
    GroveDualButton = None  # type: ignore[assignment, misc]

try:
    from grove_status_light import GroveStatusLight
    GROVE_STATUS_LIGHT_AVAILABLE = True
except ImportError:
    GROVE_STATUS_LIGHT_AVAILABLE = False
    GroveStatusLight = None  # type: ignore[assignment, misc]
# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
DEFAULT_WIDTH = 480
DEFAULT_HEIGHT = 320
PREVIEW_FPS = 2
BUTTON_WIDTH = 130
BUTTON_HEIGHT = 60
BUTTON_GAP = 15
PREVIEW_INTERVAL = 3.0  # seconds between camera frame grabs


def _load_app_config() -> dict:
    """Load config.yaml if the config module is available, else return defaults."""
    defaults = {
        "screen_width": DEFAULT_WIDTH,
        "screen_height": DEFAULT_HEIGHT,
        "camera_index": 0,
        "camera_width": 640,
        "camera_height": 480,
        "interval_seconds": 30,
        "photo_quality": 90,
        "fullscreen": False,
    }
    if CONFIG_AVAILABLE:
        try:
            cfg = load_config()
            defaults.update(cfg)
        except Exception as exc:
            logger.warning("Could not load config.yaml — using defaults: %s", exc)
    return defaults


# ═══════════════════════════════════════════════════════════════════════════
# TimeLapseApp
# ═══════════════════════════════════════════════════════════════════════════
class TimeLapseApp:
    """Main application class — owns the pygame event loop and all components."""

    def __init__(self, fullscreen: bool = False) -> None:
        # ── Config ──
        self.config = _load_app_config()
        self.screen_w: int = self.config.get("screen_width", DEFAULT_WIDTH)
        self.screen_h: int = self.config.get("screen_height", DEFAULT_HEIGHT)
        self.fullscreen = fullscreen or self.config.get("fullscreen", False)

        # ── Pygame init ──
        _init_display_driver()
        pygame.font.init()
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)
        pygame.display.set_caption("PiTimeLapse Touch")
        # Keep cursor visible while troubleshooting touch/click input mapping.
        pygame.mouse.set_visible(True)
        self.clock = pygame.time.Clock()

        # ── USB detection ──
        self.usb_path: str = "./data"
        self.usb_connected: bool = False
        self._detect_usb()

        # ── Camera ──
        self.camera: Optional[OpenCVCamera] = None  # type: ignore[assignment]
        self._init_camera()

        # ── LED controller ──
        self.led = None
        self.led_detected: bool = False
        self.led_port_name: str = ""
        self._init_led()

        # ── Grove status light (WS2813) ──
        self.grove_status_light = None
        self.grove_status_light_detected: bool = False
        self._init_grove_status_light()

        # ── Grove dual button ──
        self.grove_buttons = None
        self.grove_buttons_detected: bool = False
        self._start_stop_button: str = "button1"
        self._init_grove_buttons()
        # ── Storage & capture engine ──
        self.storage = None
        self.engine = None
        self.session = None
        self._interrupted_session = None
        self._init_backend()

        # ── App state: "main" or "settings" ──
        self._screen_state: str = "main"
        self._settings_screen: Optional[SettingsScreen] = None

        # ── UI components ──
        header_h = Header.HEIGHT       # 40
        status_h = StatusBar.HEIGHT    # 30
        button_row_h = BUTTON_HEIGHT + 20

        preview_y = header_h
        preview_h = self.screen_h - header_h - button_row_h - status_h

        # Split preview area: live camera (left) + thumbnail (right)
        preview_w = int(self.screen_w * 0.67)  # ~320px for live preview
        thumb_gap = 6
        thumb_w = self.screen_w - preview_w - thumb_gap  # ~154px for thumbnail
        
        self.header = Header(self.screen_w)
        self.preview = PreviewArea(0, preview_y, preview_w, preview_h)
        self.thumbnail = ThumbnailArea(preview_w + thumb_gap, preview_y, thumb_w, preview_h)

        # Three buttons: [START/STOP] [SETTINGS] [CLOSE]
        btn_y = header_h + preview_h + 10
        total_btn_w = BUTTON_WIDTH * 3 + BUTTON_GAP * 2
        btn_x = (self.screen_w - total_btn_w) // 2

        self.btn_start = Button(
            btn_x, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT,
            "START", COLOR_START, COLOR_TEXT, 20,
        )
        self.btn_stop = Button(
            btn_x, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT,
            "STOP", COLOR_STOP, COLOR_TEXT, 20,
        )
        self.btn_stop.visible = False

        self.btn_settings = Button(
            btn_x + BUTTON_WIDTH + BUTTON_GAP, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT,
            "SETTINGS", COLOR_SETTINGS, COLOR_TEXT, 18,
        )
        self.btn_close = Button(
            btn_x + (BUTTON_WIDTH + BUTTON_GAP) * 2, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT,
            "CLOSE", COLOR_CLOSE, COLOR_TEXT, 20,
        )

        self.status_bar = StatusBar(self.screen_w, self.screen_h)

        self._running = False
        self._capture_start_time: float = 0.0
        self._last_preview_time: float = 0.0
        self._last_thumbnail_path: str = ""  # Track last photo for thumbnail updates
        self._camera_warning: str = ""
        self._consecutive_preview_failures: int = 0
        self._preview_capture_thread: Optional[threading.Thread] = None
        self._preview_capture_started: float = 0.0
        self._preview_capture_timeout_s: float = 1.0
        self._preview_capture_lock = threading.Lock()
        self._preview_capture_result: Optional[np.ndarray] = None
        self._preview_capture_ready: bool = False

        # Display feature flags
        display_cfg = self.config.get("display", {})
        self._show_countdown: bool = display_cfg.get("show_countdown", True)
        self._show_storage_info: bool = display_cfg.get("show_storage_info", True)
        self.header.show_storage_info = self._show_storage_info
        self.header.led_detected = self.led_detected

        # Storage info state (refreshed periodically)
        self._free_gb: float = 0.0
        self._remaining_photos: int = 0
        self._last_storage_refresh: float = 0.0
        self._STORAGE_REFRESH_INTERVAL: float = 30.0

        logger.info("TimeLapseApp initialized (%dx%d, fullscreen=%s)",
                     self.screen_w, self.screen_h, self.fullscreen)

    # ── Initialization helpers ─────────────────────────────────────────────

    def _detect_usb(self) -> None:
        """Auto-pick the first USB drive; fall back to ./data."""
        if not USB_AVAILABLE:
            logger.info("usb_detector not available — saving to ./data")
            self.usb_path = "./data"
            self.usb_connected = False
            return

        try:
            path = find_first_usb_drive()
            self.usb_path = path
            info = get_drive_info(path)
            self.usb_connected = path != "./data"
            logger.info("Storage: %s (%.1f GB free)", path, info.get("free_gb", 0))
        except Exception as exc:
            logger.warning("USB detection failed: %s", exc)
            self.usb_path = "./data"
            self.usb_connected = False

    def _enumerate_camera_candidates(self, configured_index: int) -> list[int]:
        """Build a stable list of likely camera /dev/video indices.

        On Raspberry Pi, `/dev/video*` often includes codec/ISP nodes that are
        not real cameras. Probing those can appear to open successfully and then
        fail during capture with V4L2 timeouts. We therefore:

        1) Keep the configured index first (user intent always wins).
        2) Prefer sysfs devices that look like actual camera capture nodes.
        3) Fall back to low numeric indices only as a last resort.
        """

        candidates: list[int] = [configured_index]

        sysfs_devices: list[tuple[int, int, str]] = []
        for dev in glob.glob("/sys/class/video4linux/video*"):
            suffix = dev.replace("/sys/class/video4linux/video", "")
            if not suffix.isdigit():
                continue

            dev_idx = int(suffix)
            name = ""
            dev_stream_index = 0

            try:
                with open(f"{dev}/name", "r", encoding="utf-8") as f:
                    name = f.read().strip().lower()
            except Exception:
                name = ""

            try:
                with open(f"{dev}/index", "r", encoding="utf-8") as f:
                    dev_stream_index = int(f.read().strip())
            except Exception:
                dev_stream_index = 0

            sysfs_devices.append((dev_idx, dev_stream_index, name))

        # Numeric sort (video2 before video10)
        sysfs_devices.sort(key=lambda item: item[0])

        blocked_tokens = (
            "bcm2835-codec",
            "bcm2835-isp",
            "rpi-hevc",
            "metadata",
            "radio",
            "cec",
        )

        for dev_idx, dev_stream_index, name in sysfs_devices:
            if dev_idx in candidates:
                continue

            # Skip known non-camera nodes. Keep configured index exempt from
            # filtering because user may intentionally pick a special device.
            if any(tok in name for tok in blocked_tokens):
                continue

            # For multi-node devices, only probe the primary stream (index=0)
            # unless it is the explicitly configured index.
            if dev_stream_index != 0:
                continue

            candidates.append(dev_idx)

        # Conservative fallback for environments with limited /sys visibility.
        for fallback_idx in range(0, 10):
            if fallback_idx not in candidates:
                candidates.append(fallback_idx)

        return candidates

    def _init_camera(self) -> None:
        """Open the camera using OpenCV (with fallback index probing)."""
        if not CAMERA_AVAILABLE:
            logger.warning("camera_opencv not available — preview disabled")
            return
        # Close existing handle before re-initialising (e.g., after settings save)
        if self.camera is not None:
            self.camera.close()
            self.camera = None

        probe = OpenCVCamera()
        if not probe.is_available():
            logger.warning("No camera detected")
            return

        cam_cfg = self.config.get("camera", {})
        idx = int(cam_cfg.get("index", 0))
        w = int(cam_cfg.get("width", 640))
        h = int(cam_cfg.get("height", 480))

        # Try configured index first, then probe likely camera nodes.
        candidate_indices = self._enumerate_camera_candidates(idx)

        for candidate in candidate_indices:
            cam = OpenCVCamera()
            if not cam.open(candidate, w, h):
                continue

            # Validate that we can fetch a frame (codec devices can open but not stream).
            frame_ok = False
            for _ in range(3):
                frame = cam.capture()
                if frame is not None:
                    frame_ok = True
                    break
                time.sleep(0.1)

            if frame_ok:
                self.camera = cam
                self._camera_warning = ""
                self._consecutive_preview_failures = 0
                if candidate != idx:
                    logger.info(
                        "Configured camera index %d failed; using detected index %d",
                        idx,
                        candidate,
                    )
                    self.config.setdefault("camera", {})["index"] = candidate
                logger.info("Camera opened (index=%d, %dx%d)", candidate, w, h)
                return

            cam.close()

        self.camera = None
        self._camera_warning = "No camera detected"
        logger.warning("Camera failed to open on all probed indices")

    def _init_led(self) -> None:
        """Auto-detect a USB LED and ensure it starts OFF."""
        if not LED_MODULE_AVAILABLE:
            logger.info("led_controller not available — LED support disabled")
            return
        led_cfg = self.config.get("led", {})
        usb_port = led_cfg.get("usb_port", "auto")
        controller = LEDController(usb_port=usb_port)
        if controller.detect():
            controller.turn_off()  # always ensure LED starts in off state
            self.led_detected = True
            self.led_port_name = controller.port_name
            logger.info("USB LED detected on %s", controller.port_name)
            if led_cfg.get("enabled", True):
                self.led = controller
                logger.info("LED enabled for capture")
            else:
                controller.close()
                logger.info("LED disabled in config — turned off")
        else:
            logger.info("No USB LED relay found")

    def _init_grove_status_light(self) -> None:
        """Initialize optional Grove WS2813 status light."""
        if not GROVE_STATUS_LIGHT_AVAILABLE:
            logger.info("grove_status_light module not available")
            return

        cfg = self.config.get("grove_light", {})
        if not cfg.get("enabled", True):
            logger.info("Grove status light disabled in config")
            return

        pin = int(cfg.get("pin", 12))
        pixel_count = int(cfg.get("pixel_count", 10))
        brightness = int(cfg.get("brightness", 48))

        controller = GroveStatusLight(pin=pin, pixel_count=pixel_count, brightness=brightness)
        if controller.detect():
            self.grove_status_light = controller
            self.grove_status_light_detected = True
            self.grove_status_light.set_state("idle")
            logger.info("Grove WS2813 status light enabled")

    def _init_grove_buttons(self) -> None:
        """Initialize optional Grove dual button input."""
        if not GROVE_BUTTON_AVAILABLE:
            logger.info("grove_dual_button module not available")
            return

        cfg = self.config.get("grove_button", {})
        if not cfg.get("enabled", True):
            logger.info("Grove dual button disabled in config")
            return

        button1_pin = int(cfg.get("pin_button1", 5))
        button2_pin = int(cfg.get("pin_button2", 6))
        debounce_ms = int(cfg.get("debounce_ms", 250))
        self._start_stop_button = cfg.get("start_stop_button", "button1")

        controller = GroveDualButton(
            pin_button1=button1_pin,
            pin_button2=button2_pin,
            debounce_ms=debounce_ms,
        )
        if controller.detect():
            self.grove_buttons = controller
            self.grove_buttons_detected = True
            logger.info("Grove dual button enabled")

    def _poll_hardware_inputs(self) -> None:
        """Poll Grove hardware inputs and dispatch actions."""
        if self.grove_buttons is None or not self.grove_buttons.is_available():
            return

        for event in self.grove_buttons.poll_events():
            if event.button == self._start_stop_button:
                if self.engine is not None and self.engine.is_running:
                    self._on_stop()
                else:
                    self._on_start()

    def _init_backend(self) -> None:
        """Set up StorageManager and CaptureEngine; check for interrupted sessions."""
        if STORAGE_AVAILABLE:
            os.makedirs(self.usb_path, exist_ok=True)
            self.storage = StorageManager(self.usb_path)
            # Check for interrupted (crash-recovered) session
            try:
                interrupted = self.storage.find_interrupted_session()
                if interrupted:
                    self._interrupted_session = interrupted
                    logger.info("Found interrupted session: %s", interrupted.session_id)
            except Exception as exc:
                logger.warning("Could not check for interrupted sessions: %s", exc)

        if CAPTURE_ENGINE_AVAILABLE:
            self.engine = CaptureEngine()

    def _list_available_cameras(self) -> list[tuple[int, str]]:
        """Return a list of working camera devices as (index, friendly_name)."""
        if not CAMERA_AVAILABLE:
            return []

        cam_cfg = self.config.get("camera", {})
        w = int(cam_cfg.get("width", 640))
        h = int(cam_cfg.get("height", 480))

        configured_idx = int(cam_cfg.get("index", 0))
        candidate_indices = self._enumerate_camera_candidates(configured_idx)

        available: list[tuple[int, str]] = []
        for idx in candidate_indices:
            cam = OpenCVCamera()
            if not cam.open(idx, w, h):
                continue

            frame_ok = False
            for _ in range(3):
                frame = cam.capture()
                if frame is not None:
                    frame_ok = True
                    break
                time.sleep(0.1)
            cam.close()

            if not frame_ok:
                continue

            name_path = f"/sys/class/video4linux/video{idx}/name"
            name = f"video{idx}"
            if os.path.exists(name_path):
                try:
                    with open(name_path, "r", encoding="utf-8") as f:
                        name = f.read().strip() or name
                except Exception:
                    pass

            available.append((idx, name))

        return available

    # ── Main loop ──────────────────────────────────────────────────────────

    def run(self) -> None:
        """Pygame event loop — runs until quit."""
        self._running = True
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, lambda *_: self._request_quit())

        while self._running:
            self._handle_events()
            self._poll_hardware_inputs()
            self._update_preview()
            self._update_status()
            self._draw()
            self.clock.tick(PREVIEW_FPS)

        self._cleanup()

    # ── Event handling ─────────────────────────────────────────────────────

    def _handle_events(self) -> None:
        """Process pygame events (quit, touch/click)."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._request_quit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self._screen_state == "settings":
                        self._screen_state = "main"
                    else:
                        self._request_quit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self._screen_state == "settings":
                    self._handle_settings_tap(pos)
                else:
                    self._handle_main_tap(pos)

            elif event.type == pygame.FINGERDOWN:
                # Touch events provide normalized coordinates in [0.0, 1.0].
                x = max(0, min(self.screen_w - 1, int(event.x * self.screen_w)))
                y = max(0, min(self.screen_h - 1, int(event.y * self.screen_h)))
                pos = (x, y)
                if self._screen_state == "settings":
                    self._handle_settings_tap(pos)
                else:
                    self._handle_main_tap(pos)

    def _handle_main_tap(self, pos: tuple) -> None:
        """Handle taps on the main screen buttons."""
        if self.btn_start.is_pressed(pos):
            self._on_start()
        elif self.btn_stop.is_pressed(pos):
            self._on_stop()
        elif self.btn_settings.is_pressed(pos):
            self._on_settings()
        elif self.btn_close.is_pressed(pos):
            self._request_quit()

    def _handle_settings_tap(self, pos: tuple) -> None:
        """Handle taps on the settings screen."""
        if self._settings_screen is None:
            return
        action = self._settings_screen.handle_tap(pos)
        if action == "save":
            self._save_settings()
            self._screen_state = "main"
        elif action == "back":
            self._settings_screen = None
            self._screen_state = "main"

    # ── Start / Stop ───────────────────────────────────────────────────────

    def _on_start(self) -> None:
        """Begin (or resume) a timelapse capture session."""
        if self.engine is None or self.storage is None:
            logger.error("Backend modules not available — cannot start capture")
            self.status_bar.update("Error: backend missing", 0)
            return
        if self.camera is None:
            logger.error("No camera available — cannot start capture")
            self.status_bar.update("Error: no camera", 0)
            return
        if self.engine.is_running:
            return  # already running

        # Resume interrupted session or create a new one
        if self._interrupted_session is not None:
            self.session = self.storage.resume_session(self._interrupted_session)
            self._interrupted_session = None
            logger.info("Resumed session %s", self.session.session_id)
        else:
            self.session = self.storage.create_session()
            logger.info("Created session %s", self.session.session_id)

        self.engine.start(self.session, self.camera, self.storage,
                          self.config, self.led, self.grove_status_light)
        self._capture_start_time = time.time()

        if self.grove_status_light is not None:
            self.grove_status_light.set_state("capturing")
        # Swap buttons — only STOP visible while capturing
        self.btn_start.visible = False
        self.btn_stop.visible = True
        self.btn_settings.visible = False
        self.btn_close.visible = False
        self.status_bar.update("Capturing...", 0)

    def _on_stop(self) -> None:
        """Stop the current capture session."""
        if self.engine is not None and self.engine.is_running:
            self.engine.stop()
            logger.info("Capture stopped")

        # Swap buttons back
        self.btn_stop.visible = False
        self.btn_start.visible = True
        self.btn_settings.visible = True
        self.btn_close.visible = True
        self.status_bar.update("Stopped", self._elapsed())

    def _on_settings(self) -> None:
        """Open the settings screen."""
        if self.engine is not None and self.engine.is_running:
            # Don't open settings while capturing
            self.status_bar.update("Stop capture first", self._elapsed())
            return
        camera_options = self._list_available_cameras()
        self._settings_screen = SettingsScreen(
            self.screen_w, self.screen_h, self.config,
            led_detected=self.led_detected,
            led_port_name=self.led_port_name,
            camera_options=camera_options,
        )
        self._screen_state = "settings"

    def _save_settings(self) -> None:
        """Save settings from the settings screen to config.yaml and reload."""
        if self._settings_screen is None:
            return
        new_config = self._settings_screen.get_values()
        if CONFIG_AVAILABLE:
            save_config(new_config)
        self.config = _load_app_config()
        self._settings_screen = None

        # Refresh display feature flags
        display_cfg = self.config.get("display", {})
        self._show_countdown = display_cfg.get("show_countdown", True)
        self._show_storage_info = display_cfg.get("show_storage_info", True)
        self.header.show_storage_info = self._show_storage_info

        # Re-open camera using updated settings (index, resolution, etc.)
        self._init_camera()
        self._last_preview_time = 0.0

        self.status_bar.update("Settings saved", 0)
        logger.info("Settings saved")

    # ── Preview & status ───────────────────────────────────────────────────

    def _update_preview(self) -> None:
        """Grab preview frames asynchronously to keep UI responsive."""
        if self.camera is None:
            self.preview.update(None)
            return

        # If a background capture is active, avoid blocking the UI thread.
        if self._preview_capture_thread is not None and self._preview_capture_thread.is_alive():
            if (time.time() - self._preview_capture_started) > self._preview_capture_timeout_s:
                # Don't kill the worker thread (unsafe); just warn and keep UI responsive.
                self._camera_warning = "Camera timeout"
            return

        # If a worker has completed, consume its result first.
        if self._preview_capture_thread is not None and not self._preview_capture_thread.is_alive():
            frame: Optional[np.ndarray]
            with self._preview_capture_lock:
                if not self._preview_capture_ready:
                    frame = None
                else:
                    frame = self._preview_capture_result
                self._preview_capture_result = None
                self._preview_capture_ready = False

            self._preview_capture_thread = None

            if frame is None:
                self._consecutive_preview_failures += 1
                self.preview.update(None)

                if self._consecutive_preview_failures >= 3:
                    logger.warning("Camera not responding — disabling camera preview")
                    self._camera_warning = "Camera not responding"
                    self.camera.close()
                    self.camera = None
                return

            self._consecutive_preview_failures = 0
            self._camera_warning = ""
            self.preview.update(frame)
            return

        now = time.time()
        if now - self._last_preview_time < PREVIEW_INTERVAL:
            return  # reuse the last frame already in PreviewArea
        self._last_preview_time = now

        def _capture_preview_once() -> None:
            frame = None
            cam = self.camera
            if cam is not None:
                frame = cam.capture()
            with self._preview_capture_lock:
                self._preview_capture_result = frame
                self._preview_capture_ready = True

        self._preview_capture_started = now
        self._preview_capture_thread = threading.Thread(
            target=_capture_preview_once,
            name="preview-capture",
            daemon=True,
        )
        self._preview_capture_thread.start()

    def _update_status(self) -> None:
        """Refresh header and status bar from engine state."""
        photo_count = 0
        status_text = "Ready"
        elapsed = 0.0

        # Periodically refresh storage info
        if self._show_storage_info:
            now = time.time()
            if now - self._last_storage_refresh > self._STORAGE_REFRESH_INTERVAL:
                self._last_storage_refresh = now
                self._refresh_storage_info()

        if self.engine is not None and self.engine.is_running:
            st = self.engine.get_status()
            photo_count = st.get("total_photos", 0)
            elapsed = self._elapsed()
            errors = st.get("errors", [])
            
            # Update thumbnail if a new photo was captured
            last_path = st.get("last_photo_path", "")
            if last_path and last_path != self._last_thumbnail_path:
                self._last_thumbnail_path = last_path
                self.thumbnail.update_photo(last_path)
            
            if errors:
                status_text = f"Error: {errors[-1]}"
                if self.grove_status_light is not None:
                    self.grove_status_light.set_state("error")
            elif self._show_countdown:
                countdown = int(st.get("next_capture_in", 0))
                status_text = f"Next: {countdown}s"
            else:
                status_text = "Capturing..."
        elif self.engine is not None and self._capture_start_time > 0:
            st = self.engine.get_status()
            photo_count = st.get("total_photos", 0)
            elapsed = self._elapsed()
            status_text = "Stopped"
            if self.grove_status_light is not None:
                self.grove_status_light.set_state("stopped")
        elif self.camera is None:
            status_text = self._camera_warning or "No camera detected"

        self.header.update(self.usb_connected, photo_count,
                           self._free_gb, self._remaining_photos)
        self.status_bar.update(status_text, elapsed)

    def _refresh_storage_info(self) -> None:
        """Query disk usage and estimate remaining photos."""
        if not USB_AVAILABLE or not self.usb_connected:
            self._free_gb = 0.0
            self._remaining_photos = 0
            return
        try:
            info = get_drive_info(self.usb_path)
            self._free_gb = float(info.get("free_gb", 0.0))
            free_bytes = int(info.get("free_bytes", 0))

            cam = self.config.get("camera", {})
            cap = self.config.get("capture", {})
            w = cam.get("width", 640)
            h = cam.get("height", 480)
            q = cap.get("quality", 90)
            # Rough JPEG size estimate (RGB × quality / compression)
            avg_size = max(w * h * 3 * q / 100 / 10, 1024)
            self._remaining_photos = int(free_bytes / avg_size)
        except Exception:
            self._free_gb = 0.0
            self._remaining_photos = 0

    def _elapsed(self) -> float:
        """Seconds since capture started."""
        if self._capture_start_time > 0:
            return time.time() - self._capture_start_time
        return 0.0

    # ── Drawing ────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        """Render all UI components and flip the display."""
        if self._screen_state == "settings" and self._settings_screen is not None:
            self._settings_screen.draw(self.screen)
        else:
            self.screen.fill(COLOR_BACKGROUND)
            self.header.draw(self.screen)
            self.preview.draw(self.screen)
            self.thumbnail.draw(self.screen)
            self.btn_start.draw(self.screen)
            self.btn_stop.draw(self.screen)
            self.btn_settings.draw(self.screen)
            self.btn_close.draw(self.screen)
            self.status_bar.draw(self.screen)
        pygame.display.flip()

    # ── Shutdown ───────────────────────────────────────────────────────────

    def _request_quit(self) -> None:
        """Signal the main loop to exit."""
        self._running = False

    def _cleanup(self) -> None:
        """Release all resources."""
        logger.info("Shutting down…")
        if self.engine is not None and self.engine.is_running:
            self.engine.stop()
        if self.led is not None:
            self.led.close()
        if self.grove_status_light is not None:
            self.grove_status_light.close()
        if self.grove_buttons is not None:
            self.grove_buttons.close()
        if self.camera is not None:
            self.camera.close()
        pygame.quit()
        logger.info("Goodbye.")


# ═══════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════
def main() -> None:
    """Parse CLI flags and launch the app."""
    fullscreen = "--fullscreen" in sys.argv
    app = TimeLapseApp(fullscreen=fullscreen)
    try:
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        # Ensure cleanup even on unexpected exit
        if pygame.get_init():
            pygame.quit()


if __name__ == "__main__":
    main()

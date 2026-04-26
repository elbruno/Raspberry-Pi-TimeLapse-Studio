#!/usr/bin/env python3
"""
PiTimeLapse Touch — Graphical timelapse capture app for Raspberry Pi touchscreens.

Main entry point.  Wires together the camera, capture engine, storage, USB
detection, and pygame UI into a single event-loop application.

Designed for Raspberry Pi touchscreens, with Scenario 03 defaulting to an
800×450 window that fits comfortably on 800×480 DSI displays while also
running windowed on any desktop for development and testing.

Usage:
    python timelapse_touch.py              # windowed (desktop)
    python timelapse_touch.py --fullscreen # fullscreen (Pi LCD)
"""

from __future__ import annotations

import logging
import os
import platform
import signal
import subprocess
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
DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 450
PREVIEW_FPS = 2
BUTTON_WIDTH = 130
BUTTON_HEIGHT = 60
BUTTON_GAP = 15
PREVIEW_INTERVAL = 3.0  # seconds between camera frame grabs


def _load_app_config() -> dict:
    """Load config.yaml if the config module is available, else return defaults."""
    defaults = {
        "camera": {
            "mode": "opencv",
            "index": 0,
            "width": 640,
            "height": 480,
        },
        "capture": {
            "interval_seconds": 30,
            "quality": 90,
        },
        "preview": {"fps": PREVIEW_FPS},
        "storage": {"fallback_path": "./data"},
        "led": {
            "backend": "usb",
            "enabled": True,
            "warmup_seconds": 1.0,
            "usb_port": "auto",
        },
        "display": {
            "show_countdown": True,
            "show_storage_info": True,
            "window_width": DEFAULT_WIDTH,
            "window_height": DEFAULT_HEIGHT,
            "center_window": True,
            "fullscreen": False,
        },
    }
    if CONFIG_AVAILABLE:
        try:
            cfg = load_config()
            defaults.update(cfg)
        except Exception as exc:
            logger.warning("Could not load config.yaml — using defaults: %s", exc)

    # Backward compatibility for older config files.
    display_cfg = defaults.setdefault("display", {})
    if "screen_width" in defaults:
        display_cfg.setdefault("window_width", defaults.get("screen_width", DEFAULT_WIDTH))
    if "screen_height" in defaults:
        display_cfg.setdefault("window_height", defaults.get("screen_height", DEFAULT_HEIGHT))
    if "fullscreen" in defaults:
        display_cfg.setdefault("fullscreen", defaults.get("fullscreen", False))

    return defaults


# ═══════════════════════════════════════════════════════════════════════════
# TimeLapseApp
# ═══════════════════════════════════════════════════════════════════════════
class TimeLapseApp:
    """Main application class — owns the pygame event loop and all components."""

    def __init__(self, fullscreen: bool = False) -> None:
        # ── Config ──
        self.config = _load_app_config()
        display_cfg = self.config.get("display", {})
        self.screen_w = int(display_cfg.get("window_width", DEFAULT_WIDTH))
        self.screen_h = int(display_cfg.get("window_height", DEFAULT_HEIGHT))
        self._center_window = bool(display_cfg.get("center_window", True))
        self.fullscreen = fullscreen or bool(display_cfg.get("fullscreen", False))
        self.preview_fps = max(1, int(self.config.get("preview", {}).get("fps", PREVIEW_FPS)))
        self.led_backend = str(self.config.get("led", {}).get("backend", "usb")).lower()

        if not self.fullscreen and self._center_window:
            os.environ["SDL_VIDEO_CENTERED"] = "1"
            os.environ.pop("SDL_VIDEO_WINDOW_POS", None)
        else:
            os.environ.pop("SDL_VIDEO_CENTERED", None)

        # ── Pygame init ──
        _init_display_driver()
        pygame.font.init()
        flags = pygame.FULLSCREEN if self.fullscreen else 0
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h), flags)
        pygame.display.set_caption("PiTimeLapse Touch")
        display_info = pygame.display.Info()
        self.display_max_size = (
            max(self.screen_w, int(getattr(display_info, "current_w", self.screen_w) or self.screen_w)),
            max(self.screen_h, int(getattr(display_info, "current_h", self.screen_h) or self.screen_h)),
        )
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
        self.led_controller = None
        self.led_detected: bool = False
        self.led_port_name: str = ""
        self._led_test_lock = threading.Lock()
        self._led_test_active = False
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
        self._preview_updates_enabled: bool = True
        self._camera_reconnect_interval_s: float = 5.0
        self._last_camera_reconnect_attempt: float = 0.0

        # Display feature flags
        display_cfg = self.config.get("display", {})
        self._show_countdown: bool = display_cfg.get("show_countdown", True)
        self._show_storage_info: bool = display_cfg.get("show_storage_info", True)
        self.header.show_storage_info = self._show_storage_info
        self.header.led_detected = self._is_active_led_detected()

        # Storage info state (refreshed periodically)
        self._free_gb: float = 0.0
        self._remaining_photos: int = 0
        self._last_storage_refresh: float = 0.0
        self._STORAGE_REFRESH_INTERVAL: float = 30.0

        logger.info("TimeLapseApp initialized (%dx%d, fullscreen=%s, centered=%s)",
                 self.screen_w, self.screen_h, self.fullscreen, self._center_window)

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
            self._camera_warning = "Camera module unavailable"
            return
        # Close existing handle before re-initialising (e.g., after settings save)
        if self.camera is not None:
            self.camera.close()
            self.camera = None

        probe = OpenCVCamera()
        if not probe.is_available():
            logger.warning("No camera detected")
            self._camera_warning = self._camera_detection_hint()
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
        self._camera_warning = self._camera_detection_hint()
        logger.warning("Camera failed to open on all probed indices")

    def _camera_detection_hint(self) -> str:
        """Return a user-facing hint for camera detection failures."""
        # Default message (safe on all platforms)
        fallback = "No camera detected — check camera cable/power"

        if platform.system() != "Linux":
            return fallback

        try:
            result = subprocess.run(
                ["lsusb"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            lines = (result.stdout or "").lower().splitlines()
        except Exception:
            return fallback

        usb_camera_tokens = (
            "camera",
            "webcam",
            "uvc",
            "logitech",
            "microsoft",
            "sonix",
            "realtek",
            "imaging",
        )
        if any(any(tok in line for tok in usb_camera_tokens) for line in lines):
            return "Camera found on USB but stream failed — try another index"

        return fallback

    def _init_led(self) -> None:
        """Auto-detect a USB LED and ensure it starts OFF."""
        self.led_backend = str(self.config.get("led", {}).get("backend", "usb")).lower()
        if self.led_backend != "usb":
            if self.led_controller is not None:
                self.led_controller.close()
            self.led_controller = None
            self.led = None
            self.led_detected = False
            self.led_port_name = ""
            logger.info("LED backend is '%s' — skipping USB LED controller", self.led_backend)
            if hasattr(self, "header"):
                self.header.led_detected = self._is_active_led_detected()
            return

        if not LED_MODULE_AVAILABLE:
            logger.info("led_controller not available — LED support disabled")
            return

        if self.led_controller is not None:
            self.led_controller.close()
        self.led_controller = None
        self.led = None
        self.led_detected = False
        self.led_port_name = ""

        led_cfg = self.config.get("led", {})
        usb_port = led_cfg.get("usb_port", "auto")
        controller = LEDController(usb_port=usb_port)
        if controller.detect():
            controller.turn_off()  # always ensure LED starts in off state
            self.led_controller = controller
            self.led_detected = True
            self.led_port_name = controller.port_name
            logger.info("USB LED detected on %s", controller.port_name)
            if led_cfg.get("enabled", True):
                self.led = controller
                logger.info("LED enabled for capture")
            else:
                logger.info("LED disabled in config — turned off")
        else:
            logger.info("No USB LED relay found")
        if hasattr(self, "header"):
            self.header.led_detected = self._is_active_led_detected()

    def _init_grove_status_light(self) -> None:
        """Initialize optional Grove WS2813 status light."""
        if self.grove_status_light is not None:
            self.grove_status_light.close()
        self.grove_status_light = None
        self.grove_status_light_detected = False

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
        state_palette = str(cfg.get("state_palette", "classic"))
        capture_flash_duration_ms = int(cfg.get("capture_flash_duration_ms", 80))

        controller = GroveStatusLight(
            pin=pin,
            pixel_count=pixel_count,
            brightness=brightness,
            state_palette=state_palette,
            capture_flash_duration_s=max(0.02, min(1.0, capture_flash_duration_ms / 1000.0)),
        )
        # Keep a controller instance even when detect() fails so the settings
        # "DETECT" action can retry after permissions/hardware state change.
        self.grove_status_light = controller
        if controller.detect():
            self.grove_status_light_detected = True
            self.grove_status_light.set_state("off")
            logger.info("Grove WS2813 status light enabled")
        else:
            logger.info("Grove WS2813 status light present but not accessible yet")
        if hasattr(self, "header"):
            self.header.led_detected = self._is_active_led_detected()

    def _is_active_led_detected(self) -> bool:
        """Return whether the configured LED backend is available."""
        if self.led_backend == "grove":
            return self.grove_status_light_detected
        return self.led_detected

    def _init_grove_buttons(self) -> None:
        """Initialize optional Grove dual button input."""
        if not GROVE_BUTTON_AVAILABLE:
            logger.info("grove_dual_button module not available")
            return

        if self.grove_buttons is not None:
            self.grove_buttons.close()
        self.grove_buttons = None
        self.grove_buttons_detected = False

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
            logger.info("Grove button event: %s", event.button)
            if self._screen_state == "settings" and self._settings_screen is not None:
                self._settings_screen.register_hardware_button(event.button)
                continue

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
            self.clock.tick(self.preview_fps)

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
        elif action == "test_led":
            self._run_led_test()
        elif action == "detect_camera":
            self._run_camera_detect()
        elif action == "detect_led":
            self._run_led_detect()
        elif action == "back":
            self._set_preview_updates_enabled(True)
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
            self._init_camera()
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
        self._set_preview_updates_enabled(False, wait_for_thread=True)
        camera_options = self._list_available_cameras()
        self._settings_screen = SettingsScreen(
            self.screen_w, self.screen_h, self.config,
            led_detected=self.led_detected,
            led_port_name=self.led_port_name,
            camera_options=camera_options,
            grove_buttons_detected=self.grove_buttons_detected,
            led_backend=self.led_backend,
            grove_light_detected=self.grove_status_light_detected,
            max_display_size=self.display_max_size,
        )
        self._screen_state = "settings"

    def _save_settings(self) -> None:
        """Save settings from the settings screen to config.yaml and reload."""
        if self._settings_screen is None:
            return
        current_display = self.config.get("display", {})
        new_config = self._settings_screen.get_values(base_config=self.config)
        if CONFIG_AVAILABLE:
            save_config(new_config)
        self.config = _load_app_config()
        self._settings_screen = None

        # Refresh display feature flags
        display_cfg = self.config.get("display", {})
        self._show_countdown = display_cfg.get("show_countdown", True)
        self._show_storage_info = display_cfg.get("show_storage_info", True)
        self.header.show_storage_info = self._show_storage_info
        self._center_window = bool(display_cfg.get("center_window", True))
        self.preview_fps = max(1, int(self.config.get("preview", {}).get("fps", PREVIEW_FPS)))
        self.led_backend = str(self.config.get("led", {}).get("backend", "usb")).lower()

        # Re-open camera using updated settings (index, resolution, etc.)
        self._set_preview_updates_enabled(False, wait_for_thread=True)
        self._init_camera()
        self._init_led()
        self._init_grove_status_light()
        self._init_grove_buttons()
        self._set_preview_updates_enabled(True)

        restart_needed = any([
            int(current_display.get("window_width", self.screen_w)) != int(display_cfg.get("window_width", self.screen_w)),
            int(current_display.get("window_height", self.screen_h)) != int(display_cfg.get("window_height", self.screen_h)),
            bool(current_display.get("center_window", self._center_window)) != bool(display_cfg.get("center_window", self._center_window)),
            bool(current_display.get("fullscreen", self.fullscreen)) != bool(display_cfg.get("fullscreen", self.fullscreen)),
        ])
        if restart_needed:
            self.status_bar.update("Settings saved — restart to apply display size", 0)
        else:
            self.status_bar.update("Settings saved", 0)
        logger.info("Settings saved")

    def _run_led_test(self) -> None:
        """Blink the configured LED briefly from the settings screen."""
        if self._settings_screen is None:
            return

        controller = self.led_controller
        grove_light = self.grove_status_light
        if self.led_backend == "grove":
            if grove_light is None or not grove_light.is_available():
                self._settings_screen.set_hardware_message("Grove LED not available", False)
                return
        else:
            if controller is None or not controller.is_available():
                self._settings_screen.set_hardware_message("USB LED not available — check uhubctl/permissions", False)
                return

        with self._led_test_lock:
            if self._led_test_active:
                self._settings_screen.set_hardware_message("LED test already running", False)
                return
            self._led_test_active = True

        self._settings_screen.set_hardware_message("Testing LED…", True)
        self._settings_screen.set_led_test_running(True)

        def _worker() -> None:
            success = False
            test_duration_s = 2.0
            try:
                if self.led_backend == "grove":
                    grove_light.flash_test(test_duration_s)  # type: ignore[union-attr]
                    success = True
                else:
                    if controller.turn_on():  # type: ignore[union-attr]
                        time.sleep(test_duration_s)
                        success = controller.turn_off()  # type: ignore[union-attr]
                if self._settings_screen is not None:
                    if success:
                        self._settings_screen.set_hardware_message("LED test complete", True)
                    else:
                        self._settings_screen.set_hardware_message("LED test failed", False)
            finally:
                if self._settings_screen is not None:
                    self._settings_screen.set_led_test_running(False)
                with self._led_test_lock:
                    self._led_test_active = False

        threading.Thread(target=_worker, name="led-test", daemon=True).start()

    def _run_camera_detect(self) -> None:
        """Scan for available cameras and update the camera options list."""
        if self._settings_screen is None:
            return

        self._settings_screen.set_hardware_message("Scanning for cameras…", True)
        self._settings_screen.set_camera_detect_running(True)
        self._settings_screen.set_camera_preview_frame(None)

        def _worker() -> None:
            try:
                # Scan for available cameras
                available_cameras = self._list_available_cameras()
                
                if self._settings_screen is not None:
                    if available_cameras:
                        # Update camera options in settings screen
                        previous_idx = self._settings_screen.camera_options[
                            self._settings_screen._camera_selected
                        ][0]
                        self._settings_screen.camera_options = available_cameras
                        selected = 0
                        for i, (cam_idx, _) in enumerate(available_cameras):
                            if cam_idx == previous_idx:
                                selected = i
                                break
                        self._settings_screen._camera_selected = selected
                        
                        # Try to open the first camera
                        if self.camera is not None:
                            try:
                                self.camera.close()
                            except Exception as e:
                                logger.warning("Error closing existing camera: %s", e)
                        
                        idx, name = available_cameras[0]
                        cam_cfg = self.config.get("camera", {})
                        w = int(cam_cfg.get("width", 640))
                        h = int(cam_cfg.get("height", 480))
                        
                        cam = OpenCVCamera()
                        if cam.open(idx, w, h):
                            self.camera = cam
                            
                            # Capture a frame to display as preview
                            frame = None
                            for attempt in range(3):
                                frame = cam.capture()
                                if frame is not None:
                                    break
                                time.sleep(0.1)
                            
                            if frame is not None:
                                # Convert BGR to RGB for display
                                import cv2
                                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                                # Convert numpy array to pygame surface
                                pygame_frame = pygame.surfarray.make_surface(
                                    np.transpose(rgb_frame, (1, 0, 2))
                                )
                                self._settings_screen.set_camera_preview_frame(pygame_frame)
                                
                                found_count = len(available_cameras)
                                msg = f"Found {found_count} camera{'s' if found_count > 1 else ''}: {name}"
                                self._settings_screen.set_hardware_message(msg, True)
                                self._camera_warning = ""
                            else:
                                self._settings_screen.set_camera_preview_frame(None)
                                self._settings_screen.set_hardware_message(f"Camera found but frame capture failed: {name}", False)
                        else:
                            self._settings_screen.set_camera_preview_frame(None)
                            self._settings_screen.set_hardware_message(f"Found cameras but failed to open: {name}", False)
                    else:
                        configured_idx = int(self.config.get("camera", {}).get("index", 0))
                        self._settings_screen.camera_options = [(configured_idx, "Manual idx")]
                        self._settings_screen._camera_selected = 0
                        self._settings_screen.set_camera_preview_frame(None)
                        self._settings_screen.set_hardware_message("No cameras detected", False)
                        self._camera_warning = self._camera_detection_hint()
            except Exception as e:
                logger.error("Camera detection error: %s", e)
                if self._settings_screen is not None:
                    self._settings_screen.set_camera_preview_frame(None)
                    self._settings_screen.set_hardware_message(f"Error: {str(e)[:40]}", False)
            finally:
                if self._settings_screen is not None:
                    self._settings_screen.set_camera_detect_running(False)

        threading.Thread(target=_worker, name="camera-detect", daemon=True).start()

    def _run_led_detect(self) -> None:
        """Attempt to detect/reinitialize the LED from the settings screen."""
        if self._settings_screen is None:
            return

        self._settings_screen.set_hardware_message("Detecting LED…", True)
        self._settings_screen.set_led_detect_running(True)

        def _worker() -> None:
            try:
                if self.led_backend == "grove":
                    if not GROVE_STATUS_LIGHT_AVAILABLE:
                        if self._settings_screen is not None:
                            self._settings_screen.set_hardware_message("Grove driver unavailable (install rpi_ws281x)", False)
                        return

                    # Ensure controller exists (can be None if config was toggled/reloaded)
                    if self.grove_status_light is None:
                        self._init_grove_status_light()

                    grove_light = self.grove_status_light
                    if grove_light is None:
                        if self._settings_screen is not None:
                            self._settings_screen.set_hardware_message("Grove disabled in config", False)
                        return

                    # Check if running as sudo (required for Grove)
                    is_sudo = os.geteuid() == 0 if hasattr(os, 'geteuid') else False

                    # Attempt re-initialization
                    available = grove_light.detect()
                    self.grove_status_light_detected = bool(available)
                    if hasattr(self, "header"):
                        self.header.led_detected = self._is_active_led_detected()

                    if self._settings_screen is not None:
                        if available and grove_light.is_available():
                            self._settings_screen.set_hardware_message("Grove LED ✓ Detected!", True)
                            self._settings_screen.grove_light_detected = True
                        else:
                            if not is_sudo:
                                msg = "Grove needs sudo (requires /dev/mem access)"
                            else:
                                msg = "Grove LED not responding (check wiring/power)"
                            self._settings_screen.set_hardware_message(msg, False)
                            self._settings_screen.grove_light_detected = False
                else:
                    # USB LED detection
                    controller = self.led_controller
                    if controller is not None:
                        # Attempt to detect USB LED
                        available = controller.detect()
                        if self._settings_screen is not None:
                            if available:
                                self._settings_screen.set_hardware_message("USB LED ✓ Detected!", True)
                                self._settings_screen.led_detected = True
                            else:
                                self._settings_screen.set_hardware_message("USB LED: Device not found", False)
                                self._settings_screen.led_detected = False
                    else:
                        if self._settings_screen is not None:
                            self._settings_screen.set_hardware_message("LED controller not loaded", False)
            except PermissionError as e:
                logger.error("Permission denied accessing LED: %s", e)
                if self._settings_screen is not None:
                    self._settings_screen.set_hardware_message("Permission denied - try with sudo", False)
            except Exception as e:
                logger.error("LED detection error: %s", e)
                if self._settings_screen is not None:
                    self._settings_screen.set_hardware_message(f"Error: {str(e)[:35]}", False)
            finally:
                if self._settings_screen is not None:
                    self._settings_screen.set_led_detect_running(False)

        threading.Thread(target=_worker, name="led-detect", daemon=True).start()

    # ── Preview & status ───────────────────────────────────────────────────

    def _clear_preview_capture_state(self) -> None:
        """Clear any cached preview capture result or worker bookkeeping."""
        with self._preview_capture_lock:
            self._preview_capture_result = None
            self._preview_capture_ready = False
        if self._preview_capture_thread is not None and not self._preview_capture_thread.is_alive():
            self._preview_capture_thread = None

    def _set_preview_updates_enabled(self, enabled: bool, wait_for_thread: bool = False) -> None:
        """Pause or resume camera preview refreshes.

        When disabling, optionally wait for the current one-shot capture worker to
        finish so camera reconfiguration does not race with an in-flight preview.
        """
        self._preview_updates_enabled = enabled

        if not enabled:
            if wait_for_thread and self._preview_capture_thread is not None:
                self._preview_capture_thread.join(timeout=self._preview_capture_timeout_s + 0.1)
                if self._preview_capture_thread.is_alive():
                    logger.warning("Preview capture thread still running while preview is paused")
            self._clear_preview_capture_state()
            return

        self._last_preview_time = 0.0
        self._clear_preview_capture_state()

    def _update_preview(self) -> None:
        """Grab preview frames asynchronously to keep UI responsive."""
        if not self._preview_updates_enabled:
            return

        if self.camera is None:
            if self._screen_state != "settings" and not (self.engine and self.engine.is_running):
                now = time.time()
                if now - self._last_camera_reconnect_attempt >= self._camera_reconnect_interval_s:
                    self._last_camera_reconnect_attempt = now
                    logger.info("Camera unavailable — attempting reconnect")
                    self._init_camera()
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
                    self._last_camera_reconnect_attempt = 0.0
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
                self.grove_status_light.set_state("off")
        elif self.camera is None:
            status_text = self._camera_warning or "No camera detected"
            if self.grove_status_light is not None:
                self.grove_status_light.set_state("off")
        else:
            if self.grove_status_light is not None:
                self.grove_status_light.set_state("off")

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
        if self.led_controller is not None:
            self.led_controller.close()
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

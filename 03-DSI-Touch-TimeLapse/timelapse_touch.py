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
import socket
import subprocess
import sys
import threading
import time
import glob
from typing import Optional
from urllib.parse import urlparse

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
            "source_mode": "daemon_primary",
            "index": 0,
            "width": 640,
            "height": 480,
            "daemon": {
                "enabled": True,
                "rtsp_url": "rtsp://127.0.0.1:8554/unicast",
                "open_timeout_s": 5.0,
                "read_timeout_s": 3.0,
                "healthcheck_interval_s": 5.0,
                "healthcheck_timeout_s": 2.0,
                "connect_transport": "tcp",
            },
        },
        "capture": {
            "interval_seconds": 30,
            "quality": 90,
        },
        "preview": {"fps": PREVIEW_FPS},
        "storage": {"fallback_path": "./data"},
        "led": {
            "enabled": True,
            "warmup_seconds": 1.5,
            "pre_capture_lead_seconds": 0.0,
        },
        "grove_relay": {
            "enabled": True,
            "pin": 26,
            "active_high": True,
        },
        "grove_relay_2": {
            "enabled": True,
            "pin": 24,
            "active_high": True,
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
        self._active_camera_source: str = "none"
        self._camera_on_hold: bool = False
        self._camera_on_hold_reason: str = ""
        self._camera_on_hold_since: float = 0.0
        self._camera_last_frame_ok_ts: float = 0.0
        self._camera_reconnect_thread: Optional[threading.Thread] = None
        daemon_cfg = self.config.get("camera", {}).get("daemon", {})
        self._camera_healthcheck_interval_s: float = float(
            daemon_cfg.get("healthcheck_interval_s", 5.0)
        )
        self._camera_healthcheck_timeout_s: float = float(
            daemon_cfg.get("healthcheck_timeout_s", 2.0)
        )
        self._last_camera_healthcheck_attempt: float = 0.0
        self._init_camera()

        # ── Relay controller ──
        self.led = None
        self.led_controller = None
        self.led_detected: bool = False
        self.led_port_name: str = ""
        self.relay_2 = None
        self.relay_2_controller = None
        self.relay_2_detected: bool = False
        self.relay_2_port_name: str = ""
        self._led_test_lock = threading.Lock()
        self._led_test_active = False
        self._relay_2_test_lock = threading.Lock()
        self._relay_2_test_active = False
        self._init_led()
        self._init_relay_2()

        # ── Grove dual button ──
        self.grove_buttons = None
        self.grove_buttons_detected: bool = False
        self._start_stop_button: str = "button1"
        self._stop_button: str = ""
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
        self.header.led_detected = self.led_detected
        self.header.relay_2_detected = self.relay_2_detected

        # Storage info state (refreshed periodically)
        self._free_gb: float = 0.0
        self._remaining_photos: int = 0
        self._last_storage_refresh: float = 0.0
        self._STORAGE_REFRESH_INTERVAL: float = 30.0

        # Camera index validation (for settings screen real-time feedback)
        self._camera_index_validation_running: bool = False
        self._last_validated_camera_index: int = int(self.config.get("camera", {}).get("index", 0))

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

        candidates: list[int] = []
        # User intent first — but only if the device node actually exists,
        # to avoid probing dead indices after replug.
        if os.path.exists(f"/dev/video{configured_index}") or platform.system() != "Linux":
            candidates.append(configured_index)

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

        secondary_candidates: list[int] = []

        for dev_idx, dev_stream_index, name in sysfs_devices:
            if dev_idx in candidates:
                continue

            # Skip known non-camera nodes. Keep configured index exempt from
            # filtering because user may intentionally pick a special device.
            if any(tok in name for tok in blocked_tokens):
                continue

            # Prefer primary stream nodes first, but keep secondary streams as
            # fallback because some camera stacks expose the usable stream on
            # non-zero indices.
            if dev_stream_index == 0:
                candidates.append(dev_idx)
            else:
                secondary_candidates.append(dev_idx)

        for dev_idx in secondary_candidates:
            if dev_idx not in candidates:
                candidates.append(dev_idx)

        # Conservative fallback: only scan low indices (0-9) when sysfs gave
        # us nothing usable. Probing 10-19 wastes time and rarely helps.
        if len(candidates) <= 1:
            for fallback_idx in range(0, 10):
                if fallback_idx not in candidates:
                    candidates.append(fallback_idx)

        return candidates

    def _init_camera(self) -> None:
        """Open the camera using selected source mode with fallback policy.

        Source order is controlled by ``camera.source_mode``:
        - ``daemon_primary``: daemon stream first, then direct /dev/video fallback.
        - ``direct_primary``: direct first, then daemon stream fallback.
        - ``direct_only``: direct only (legacy behavior).
        """
        if not CAMERA_AVAILABLE:
            logger.warning("camera_opencv not available — preview disabled")
            self._camera_warning = "Camera module unavailable"
            self._active_camera_source = "none"
            return
        # Close existing handle before re-initialising (e.g., after settings save)
        if self.camera is not None:
            self.camera.close()
            self.camera = None

        probe = OpenCVCamera()
        if not probe.is_available():
            logger.warning("No camera detected")
            self._camera_warning = self._camera_detection_hint()
            self._active_camera_source = "none"
            return

        cam_cfg = self.config.get("camera", {})
        idx = int(cam_cfg.get("index", 0))
        w = int(cam_cfg.get("width", 640))
        h = int(cam_cfg.get("height", 480))
        source_mode = str(cam_cfg.get("source_mode", "daemon_primary")).strip().lower()
        if source_mode not in ("daemon_primary", "direct_primary", "direct_only"):
            logger.warning("Invalid camera.source_mode '%s' — using daemon_primary", source_mode)
            source_mode = "daemon_primary"

        daemon_cfg = cam_cfg.get("daemon", {}) if isinstance(cam_cfg, dict) else {}
        daemon_enabled = bool(daemon_cfg.get("enabled", True))
        daemon_url = str(
            daemon_cfg.get("rtsp_url", "rtsp://127.0.0.1:8554/unicast")
        ).strip()
        daemon_open_timeout = float(daemon_cfg.get("open_timeout_s", 5.0))
        if not daemon_url:
            daemon_url = "rtsp://127.0.0.1:8554/unicast"

        source_order: list[str] = []
        if source_mode == "direct_only":
            source_order = ["direct"]
        elif source_mode == "direct_primary":
            source_order = ["direct", "daemon"]
        else:
            source_order = ["daemon", "direct"]

        def _validate_stream(cam: OpenCVCamera) -> bool:
            for _ in range(3):
                frame = cam.capture()
                if frame is not None:
                    return True
                time.sleep(0.1)
            return False

        for source_kind in source_order:
            if source_kind == "daemon":
                if not daemon_enabled:
                    continue

                if not self._is_daemon_endpoint_reachable(daemon_url, daemon_open_timeout):
                    logger.warning("Daemon endpoint not reachable: %s", daemon_url)
                    continue

                cam = OpenCVCamera()
                if not cam.open(width=w, height=h, source="daemon", stream_url=daemon_url):
                    continue

                if _validate_stream(cam):
                    self.camera = cam
                    self._camera_warning = ""
                    self._consecutive_preview_failures = 0
                    self._active_camera_source = "daemon"
                    self._camera_last_frame_ok_ts = time.time()
                    self._clear_camera_on_hold()
                    logger.info(
                        "Camera opened via daemon stream (%s, %dx%d)",
                        daemon_url,
                        w,
                        h,
                    )
                    return

                cam.close()
                continue

            # Direct source path (legacy /dev/video probing).
            candidate_indices = self._enumerate_camera_candidates(idx)
            for candidate in candidate_indices:
                cam = OpenCVCamera()
                if not cam.open(candidate, w, h, source="direct"):
                    continue

                if _validate_stream(cam):
                    self.camera = cam
                    self._camera_warning = ""
                    self._consecutive_preview_failures = 0
                    self._active_camera_source = "direct"
                    self._camera_last_frame_ok_ts = time.time()
                    self._clear_camera_on_hold()
                    if source_mode == "daemon_primary":
                        logger.info(
                            "Daemon source unavailable; using direct camera index %d",
                            candidate,
                        )
                    elif candidate != idx:
                        logger.info(
                            "Configured camera index %d failed; using detected index %d",
                            idx,
                            candidate,
                        )
                    logger.info(
                        "Camera opened via direct device (index=%d, %dx%d)",
                        candidate,
                        w,
                        h,
                    )
                    return

                cam.close()

        self.camera = None
        self._active_camera_source = "none"
        self._camera_warning = self._camera_detection_hint()
        self._set_camera_on_hold("Camera source unavailable — recovering")
        logger.warning(
            "Camera failed to open for source_mode=%s (daemon_enabled=%s)",
            source_mode,
            daemon_enabled,
        )

    def _reopen_camera_for_engine(self) -> Optional[OpenCVCamera]:
        """Callback used by the capture engine to recover from a camera loss.

        Re-runs the standard ``_init_camera`` probe. Returns the new camera
        handle (so the engine can swap it in) or ``None`` if probing failed.

        This runs in the capture engine's background thread, so it must not
        touch pygame UI state directly. ``_init_camera`` only mutates
        ``self.camera`` / ``self.config`` / ``self._camera_warning``, all of
        which are safe to update from another thread for our usage.
        """
        try:
            self._init_camera()
        except Exception as exc:
            logger.warning("Camera reopen failed: %s", exc)
            return None
        return self.camera

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

    def _is_daemon_endpoint_reachable(self, stream_url: str, timeout_s: float) -> bool:
        """Quick readiness check for daemon stream endpoint.

        For RTSP/HTTP-style URLs this validates that host:port is reachable
        before OpenCV attempts opening the stream.
        """
        if not stream_url:
            return False

        parsed = urlparse(stream_url)
        scheme = (parsed.scheme or "").lower()
        if scheme not in ("rtsp", "http", "https", "tcp"):
            return True

        host = parsed.hostname
        if not host:
            return False

        if parsed.port is not None:
            port = parsed.port
        elif scheme == "rtsp":
            port = 554
        elif scheme == "https":
            port = 443
        else:
            port = 80

        try:
            with socket.create_connection((host, port), timeout=max(0.2, float(timeout_s))):
                return True
        except Exception:
            return False

    def _set_camera_on_hold(self, reason: str) -> None:
        """Set camera ON HOLD state with a user-facing reason."""
        self._camera_on_hold = True
        self._camera_on_hold_reason = reason.strip() or "Camera recovering"
        self._camera_on_hold_since = time.time()

    def _clear_camera_on_hold(self) -> None:
        """Clear camera ON HOLD state after successful recovery."""
        self._camera_on_hold = False
        self._camera_on_hold_reason = ""
        self._camera_on_hold_since = 0.0

    def _start_async_camera_reconnect(self, reason: str = "") -> None:
        """Trigger camera reconnect in background to avoid UI blocking."""
        if self._camera_reconnect_thread is not None and self._camera_reconnect_thread.is_alive():
            return

        self._set_camera_on_hold(reason or "Camera reconnect in progress")

        def _worker() -> None:
            try:
                self._init_camera()
            except Exception as exc:
                logger.warning("Async camera reconnect failed: %s", exc)
                self._set_camera_on_hold("Camera reconnect failed")

        self._camera_reconnect_thread = threading.Thread(
            target=_worker,
            name="camera-reconnect",
            daemon=True,
        )
        self._camera_reconnect_thread.start()

    def _init_led(self) -> None:
        """Initialize Grove relay controller and ensure it starts OFF."""
        if not LED_MODULE_AVAILABLE:
            logger.info("led_controller not available — LED support disabled")
            return

        if self.led_controller is not None:
            self.led_controller.close()
        self.led_controller = None
        self.led = None
        self.led_detected = False
        self.led_port_name = ""

        relay_cfg = self.config.get("grove_relay", {})
        if not relay_cfg.get("enabled", True):
            logger.info("Grove relay disabled in config")
            if hasattr(self, "header"):
                self.header.led_detected = False
            return

        led_cfg = self.config.get("led", {})
        pin = int(relay_cfg.get("pin", 26))
        active_high = bool(relay_cfg.get("active_high", True))
        controller = LEDController(pin=pin, active_high=active_high)
        if controller.detect():
            controller.turn_off()  # always ensure LED starts in off state
            self.led_controller = controller
            self.led_detected = True
            self.led_port_name = controller.port_name
            logger.info("Grove relay detected on %s", controller.port_name)
            if led_cfg.get("enabled", True):
                self.led = controller
                logger.info("Relay enabled for capture")
            else:
                logger.info("Relay disabled in config — kept OFF")
        else:
            logger.info("No Grove relay found")
        if hasattr(self, "header"):
            self.header.led_detected = self.led_detected

    def _init_relay_2(self) -> None:
        """Initialize optional second Grove relay controller and ensure it starts OFF."""
        if not LED_MODULE_AVAILABLE:
            logger.info("led_controller not available — relay #2 support disabled")
            return

        if self.relay_2_controller is not None:
            self.relay_2_controller.close()
        self.relay_2_controller = None
        self.relay_2 = None
        self.relay_2_detected = False
        self.relay_2_port_name = ""

        relay_cfg = self.config.get("grove_relay_2", {})
        if not relay_cfg.get("enabled", True):
            logger.info("Grove relay #2 disabled in config")
            if hasattr(self, "header"):
                self.header.relay_2_detected = False
            return

        led_cfg = self.config.get("led", {})
        pin = int(relay_cfg.get("pin", 24))
        active_high = bool(relay_cfg.get("active_high", True))
        controller = LEDController(pin=pin, active_high=active_high)
        if controller.detect():
            controller.turn_off()
            self.relay_2_controller = controller
            self.relay_2_detected = True
            self.relay_2_port_name = controller.port_name
            logger.info("Grove relay #2 detected on %s", controller.port_name)
            if led_cfg.get("enabled", True):
                self.relay_2 = controller
                logger.info("Relay #2 enabled for capture")
            else:
                logger.info("Relay #2 disabled by led.enabled — kept OFF")
        else:
            logger.info("No Grove relay #2 found")
        if hasattr(self, "header"):
            self.header.relay_2_detected = self.relay_2_detected

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
        self._stop_button = cfg.get("stop_button", "") or ""

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
            elif event.button == self._stop_button:
                # Dedicated STOP button: only acts when capture is running.
                if self.engine is not None and self.engine.is_running:
                    self._on_stop()

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

    def _list_available_cameras(
        self,
        progress_cb: Optional["callable"] = None,
        stop_on_first: bool = False,
    ) -> list[tuple[int, str]]:
        """Return a list of working camera devices as (index, friendly_name).

        Args:
            progress_cb: Optional callback(idx: int, total: int, current: int) called
                         before probing each candidate. Lets the UI report progress.
            stop_on_first: If True, return as soon as one working camera is found.
                          Use for fast detection (main app startup); use False for
                          full enumeration (settings DETECT button).
        """
        if not CAMERA_AVAILABLE:
            return []

        cam_cfg = self.config.get("camera", {})
        w = int(cam_cfg.get("width", 640))
        h = int(cam_cfg.get("height", 480))

        configured_idx = int(cam_cfg.get("index", 0))
        candidate_indices = self._enumerate_camera_candidates(configured_idx)

        available: list[tuple[int, str]] = []
        total = len(candidate_indices)

        for position, idx in enumerate(candidate_indices, start=1):
            if progress_cb is not None:
                try:
                    progress_cb(idx, total, position)
                except Exception:
                    pass  # Progress callback errors should never abort scan

            # Skip indices where /dev/videoN doesn't exist on Linux. Avoids 
            # waiting for V4L2 timeout on phantom indices after replug.
            if platform.system() == "Linux" and not os.path.exists(f"/dev/video{idx}"):
                continue

            cam = OpenCVCamera()
            # Two-phase probe: fast attempt, then a slower retry for newly
            # connected devices that need time to settle.
            opened = False
            for attempt in range(2):
                if cam.open(idx, w, h):
                    opened = True
                    break
                if attempt == 0:
                    time.sleep(0.15)

            if not opened:
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
            if stop_on_first:
                break

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
            self._check_camera_index_validation()  # Real-time camera index feedback in settings
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
        elif action == "test_relay_2":
            self._run_relay_2_test()
        elif action == "detect_relay_2":
            self._run_relay_2_detect()
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
                          self.config, self.led,
                          relay_2=self.relay_2,
                          camera_reopen_callback=self._reopen_camera_for_engine)
        self._capture_start_time = time.time()
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
            relay_2_detected=self.relay_2_detected,
            relay_2_port_name=self.relay_2_port_name,
            camera_options=camera_options,
            grove_buttons_detected=self.grove_buttons_detected,
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

        # Re-open camera using updated settings (index, resolution, etc.)
        self._set_preview_updates_enabled(False, wait_for_thread=True)
        self._init_camera()
        self._init_led()
        self._init_relay_2()
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
        if controller is None or not controller.is_available():
            self._settings_screen.set_hardware_message("Relay not available", False)
            return

        with self._led_test_lock:
            if self._led_test_active:
                self._settings_screen.set_hardware_message("LED test already running", False)
                return
            self._led_test_active = True

        self._settings_screen.set_hardware_message("Testing relay…", True)
        self._settings_screen.set_led_test_running(True)

        def _worker() -> None:
            success = False
            test_duration_s = 2.0
            try:
                if controller.turn_on():  # type: ignore[union-attr]
                    time.sleep(test_duration_s)
                    success = controller.turn_off()  # type: ignore[union-attr]
                if self._settings_screen is not None:
                    if success:
                        self._settings_screen.set_hardware_message("Relay test complete", True)
                    else:
                        self._settings_screen.set_hardware_message("Relay test failed", False)
            finally:
                if self._settings_screen is not None:
                    self._settings_screen.set_led_test_running(False)
                with self._led_test_lock:
                    self._led_test_active = False

        threading.Thread(target=_worker, name="led-test", daemon=True).start()

    def _run_relay_2_test(self) -> None:
        """Blink relay #2 briefly from the settings screen."""
        if self._settings_screen is None:
            return

        controller = self.relay_2_controller
        if controller is None or not controller.is_available():
            self._settings_screen.set_hardware_message("Relay #2 not available", False)
            return

        with self._relay_2_test_lock:
            if self._relay_2_test_active:
                self._settings_screen.set_hardware_message("Relay #2 test already running", False)
                return
            self._relay_2_test_active = True

        self._settings_screen.set_hardware_message("Testing relay #2…", True)
        self._settings_screen.set_relay_2_test_running(True)

        def _worker() -> None:
            success = False
            test_duration_s = 2.0
            try:
                if controller.turn_on():  # type: ignore[union-attr]
                    time.sleep(test_duration_s)
                    success = controller.turn_off()  # type: ignore[union-attr]
                if self._settings_screen is not None:
                    if success:
                        self._settings_screen.set_hardware_message("Relay #2 test complete", True)
                    else:
                        self._settings_screen.set_hardware_message("Relay #2 test failed", False)
            finally:
                if self._settings_screen is not None:
                    self._settings_screen.set_relay_2_test_running(False)
                with self._relay_2_test_lock:
                    self._relay_2_test_active = False

        threading.Thread(target=_worker, name="relay2-test", daemon=True).start()

    def _run_camera_detect(self) -> None:
        """Scan for available cameras and update the camera options list.

        Strategy for robust detection (especially after USB unplug/replug):
        1. Release any currently-held camera handle so the device is free.
        2. Brief settle delay to let USB enumeration complete.
        3. Probe candidates with live progress feedback.
        4. If main scan finds nothing, do a second pass after a longer wait
           to catch slow-enumerating USB cameras.
        5. Save working index to config immediately for future startups.
        """
        if self._settings_screen is None:
            return

        self._settings_screen.set_hardware_message("Releasing camera…", True)
        self._settings_screen.set_camera_detect_running(True)
        self._settings_screen.set_camera_preview_frame(None)

        def _worker() -> None:
            try:
                # Step 1: ALWAYS release the main camera before scanning. A held
                # handle blocks reprobe and prevents detection of replugged devices.
                if self.camera is not None:
                    try:
                        self.camera.close()
                    except Exception as e:
                        logger.warning("Error closing existing camera: %s", e)
                    self.camera = None

                # Pause preview updates while detection runs to avoid races.
                self._set_preview_updates_enabled(False)

                # Step 2: Settle delay — allows USB enumeration after replug.
                self._settings_screen.set_hardware_message("Waiting for USB…", True)
                time.sleep(0.5)

                # Step 3: Progress callback updates UI as we probe each index.
                def _progress(idx: int, total: int, position: int) -> None:
                    if self._settings_screen is not None:
                        self._settings_screen.set_hardware_message(
                            f"Probing /dev/video{idx} ({position}/{total})…", True
                        )

                # First pass — fast scan.
                available_cameras = self._list_available_cameras(
                    progress_cb=_progress, stop_on_first=False
                )

                # Step 4: Second pass with longer wait if first found nothing.
                # Helps for slow-binding USB drivers after replug.
                if not available_cameras:
                    if self._settings_screen is not None:
                        self._settings_screen.set_hardware_message(
                            "Retry — waiting for camera…", True
                        )
                    time.sleep(1.5)
                    available_cameras = self._list_available_cameras(
                        progress_cb=_progress, stop_on_first=False
                    )

                if self._settings_screen is None:
                    return

                if not available_cameras:
                    configured_idx = int(self.config.get("camera", {}).get("index", 0))
                    self._settings_screen.camera_options = [(configured_idx, "Manual idx")]
                    self._settings_screen._camera_selected = 0
                    self._settings_screen.set_camera_preview_frame(None)
                    self._settings_screen.set_hardware_message(
                        "No cameras found — check USB cable", False
                    )
                    self._camera_warning = self._camera_detection_hint()
                    return

                # Step 5: Update settings UI with discovered cameras.
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

                # Update Cam Index stepper to reflect the first available camera
                first_idx, first_name = available_cameras[0]
                for row in self._settings_screen.camera_rows:
                    if row.key == "camera.index":
                        row.value = first_idx
                        # Update validation tracker so it doesn't re-probe immediately
                        self._last_validated_camera_index = first_idx
                        break

                # Step 6: Open the first found camera and capture preview frame.
                cam_cfg = self.config.get("camera", {})
                w = int(cam_cfg.get("width", 640))
                h = int(cam_cfg.get("height", 480))

                cam = OpenCVCamera()
                if not cam.open(first_idx, w, h):
                    self._settings_screen.set_hardware_message(
                        f"Found {first_name} but failed to open", False
                    )
                    return

                self.camera = cam
                # Persist the working index so startup uses it next time
                self.config.setdefault("camera", {})["index"] = first_idx

                # Capture a frame for the preview area
                frame = None
                for _ in range(3):
                    frame = cam.capture()
                    if frame is not None:
                        break
                    time.sleep(0.1)

                if frame is not None:
                    import cv2
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pygame_frame = pygame.surfarray.make_surface(
                        np.transpose(rgb_frame, (1, 0, 2))
                    )
                    self._settings_screen.set_camera_preview_frame(pygame_frame)
                    found_count = len(available_cameras)
                    msg = f"Found {found_count} camera{'s' if found_count > 1 else ''}: {first_name}"
                    self._settings_screen.set_hardware_message(msg, True)
                    self._camera_warning = ""
                else:
                    self._settings_screen.set_camera_preview_frame(None)
                    self._settings_screen.set_hardware_message(
                        f"Opened {first_name} but no frame", False
                    )
            except Exception as e:
                logger.error("Camera detection error: %s", e)
                if self._settings_screen is not None:
                    self._settings_screen.set_camera_preview_frame(None)
                    self._settings_screen.set_hardware_message(f"Error: {str(e)[:40]}", False)
            finally:
                if self._settings_screen is not None:
                    self._settings_screen.set_camera_detect_running(False)
                # Re-enable preview updates so the main loop can resume
                self._set_preview_updates_enabled(True)

        threading.Thread(target=_worker, name="camera-detect", daemon=True).start()

    def _check_camera_index_validation(self) -> None:
        """Check if camera index has changed in settings and validate it.
        
        Runs in the background to provide live per-index feedback while the user
        adjusts the index selector in the settings screen.
        """
        if self._settings_screen is None or self._camera_index_validation_running:
            return

        # Find the camera index row in camera_rows
        camera_index_row = None
        for row in self._settings_screen.camera_rows:
            if row.key == "camera.index":
                camera_index_row = row
                break

        if camera_index_row is None:
            return

        current_index = camera_index_row.value
        if current_index == self._last_validated_camera_index:
            return  # No change

        self._last_validated_camera_index = current_index
        self._camera_index_validation_running = True

        def _validate_worker() -> None:
            try:
                cam_cfg = self.config.get("camera", {})
                w = int(cam_cfg.get("width", 640))
                h = int(cam_cfg.get("height", 480))

                cam = OpenCVCamera()
                if cam.open(current_index, w, h):
                    # Try to capture a frame to validate the camera works
                    frame = None
                    for attempt in range(2):
                        frame = cam.capture()
                        if frame is not None:
                            break
                        time.sleep(0.05)

                    cam.close()

                    if frame is not None:
                        if self._settings_screen is not None:
                            self._settings_screen.set_hardware_message(
                                f"Index {current_index}: ✓ OK", True
                            )
                    else:
                        if self._settings_screen is not None:
                            self._settings_screen.set_hardware_message(
                                f"Index {current_index}: ✗ No frame", False
                            )
                else:
                    if self._settings_screen is not None:
                        self._settings_screen.set_hardware_message(
                            f"Index {current_index}: ✗ Failed to open", False
                        )
            except Exception as e:
                logger.warning("Camera index validation error for index %d: %s", current_index, e)
                if self._settings_screen is not None:
                    self._settings_screen.set_hardware_message(
                        f"Index {current_index}: ✗ Error", False
                    )
            finally:
                self._camera_index_validation_running = False

        threading.Thread(target=_validate_worker, name="camera-index-validate", daemon=True).start()

    def _run_led_detect(self) -> None:
        """Attempt to detect/reinitialize the relay from the settings screen."""
        if self._settings_screen is None:
            return

        self._settings_screen.set_hardware_message("Detecting relay…", True)
        self._settings_screen.set_led_detect_running(True)

        def _worker() -> None:
            try:
                relay_cfg = self.config.get("grove_relay", {})
                if self.led_controller is None:
                    pin = int(relay_cfg.get("pin", 26))
                    active_high = bool(relay_cfg.get("active_high", True))
                    self.led_controller = LEDController(pin=pin, active_high=active_high)

                controller = self.led_controller
                available = bool(controller and controller.detect())
                self.led_detected = available
                if available and controller is not None:
                    self.led_port_name = controller.port_name
                    if self.config.get("led", {}).get("enabled", True):
                        self.led = controller
                if hasattr(self, "header"):
                    self.header.led_detected = self.led_detected

                if self._settings_screen is not None:
                    self._settings_screen.led_detected = available
                    if available:
                        self._settings_screen.set_hardware_message("Relay ✓ Detected!", True)
                    else:
                        self._settings_screen.set_hardware_message("Relay not detected (check wiring/sudo)", False)
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

    def _run_relay_2_detect(self) -> None:
        """Attempt to detect/reinitialize relay #2 from the settings screen."""
        if self._settings_screen is None:
            return

        self._settings_screen.set_hardware_message("Detecting relay #2…", True)
        self._settings_screen.set_relay_2_detect_running(True)

        def _worker() -> None:
            try:
                relay_cfg = self.config.get("grove_relay_2", {})
                if self.relay_2_controller is None:
                    pin = int(relay_cfg.get("pin", 24))
                    active_high = bool(relay_cfg.get("active_high", True))
                    self.relay_2_controller = LEDController(pin=pin, active_high=active_high)

                controller = self.relay_2_controller
                available = bool(controller and controller.detect())
                self.relay_2_detected = available
                if available and controller is not None:
                    self.relay_2_port_name = controller.port_name
                    if self.config.get("led", {}).get("enabled", True):
                        self.relay_2 = controller
                if hasattr(self, "header"):
                    self.header.relay_2_detected = self.relay_2_detected

                if self._settings_screen is not None:
                    self._settings_screen.relay_2_detected = available
                    if available:
                        self._settings_screen.set_hardware_message("Relay #2 ✓ Detected!", True)
                    else:
                        self._settings_screen.set_hardware_message("Relay #2 not detected (check wiring/sudo)", False)
            except PermissionError as e:
                logger.error("Permission denied accessing relay #2: %s", e)
                if self._settings_screen is not None:
                    self._settings_screen.set_hardware_message("Permission denied - try with sudo", False)
            except Exception as e:
                logger.error("Relay #2 detection error: %s", e)
                if self._settings_screen is not None:
                    self._settings_screen.set_hardware_message(f"Error: {str(e)[:35]}", False)
            finally:
                if self._settings_screen is not None:
                    self._settings_screen.set_relay_2_detect_running(False)

        threading.Thread(target=_worker, name="relay2-detect", daemon=True).start()

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
                    logger.info("Camera unavailable — attempting async reconnect")
                    self._start_async_camera_reconnect("Camera unavailable")
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
                    self._camera_warning = "Camera not responding — recovering"
                    self.camera.close()
                    self.camera = None
                    self._set_camera_on_hold("Camera stream stalled")
                    self._last_camera_reconnect_attempt = 0.0
                return

            self._consecutive_preview_failures = 0
            self._camera_warning = ""
            self._camera_last_frame_ok_ts = time.time()
            self._clear_camera_on_hold()
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
        elif self._camera_on_hold:
            status_text = f"ON HOLD: {self._camera_on_hold_reason}"
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
        if self.led_controller is not None:
            self.led_controller.close()
        if self.relay_2_controller is not None:
            self.relay_2_controller.close()
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

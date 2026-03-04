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
import time
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
    StatusBar,
    COLOR_BACKGROUND,
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
    from config import load_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

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
PREVIEW_FPS = 6
BUTTON_WIDTH = 180
BUTTON_HEIGHT = 80


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
        self.clock = pygame.time.Clock()

        # ── USB detection ──
        self.usb_path: str = "./data"
        self.usb_connected: bool = False
        self._detect_usb()

        # ── Camera ──
        self.camera: Optional[OpenCVCamera] = None  # type: ignore[assignment]
        self._init_camera()

        # ── Storage & capture engine ──
        self.storage = None
        self.engine = None
        self.session = None
        self._interrupted_session = None
        self._init_backend()

        # ── UI components ──
        header_h = Header.HEIGHT       # 40
        status_h = StatusBar.HEIGHT    # 30
        button_row_h = BUTTON_HEIGHT + 20  # 100 (80 btn + padding)

        preview_y = header_h
        preview_h = self.screen_h - header_h - button_row_h - status_h

        self.header = Header(self.screen_w)
        self.preview = PreviewArea(0, preview_y, self.screen_w, preview_h)

        btn_y = header_h + preview_h + 10
        gap = 20
        total_btn_w = BUTTON_WIDTH * 2 + gap
        btn_x = (self.screen_w - total_btn_w) // 2

        self.btn_start = Button(
            btn_x, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT,
            "START", COLOR_START, COLOR_TEXT, 24,
        )
        self.btn_stop = Button(
            btn_x + BUTTON_WIDTH + gap, btn_y, BUTTON_WIDTH, BUTTON_HEIGHT,
            "STOP", COLOR_STOP, COLOR_TEXT, 24,
        )
        self.btn_stop.visible = False  # hidden until capture starts

        self.status_bar = StatusBar(self.screen_w, self.screen_h)

        self._running = False
        self._capture_start_time: float = 0.0

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

    def _init_camera(self) -> None:
        """Open the camera using OpenCV."""
        if not CAMERA_AVAILABLE:
            logger.warning("camera_opencv not available — preview disabled")
            return
        cam = OpenCVCamera()
        if cam.is_available():
            idx = self.config.get("camera_index", 0)
            w = self.config.get("camera_width", 640)
            h = self.config.get("camera_height", 480)
            if cam.open(idx, w, h):
                self.camera = cam
                logger.info("Camera opened (index=%d, %dx%d)", idx, w, h)
            else:
                logger.warning("Camera failed to open")
        else:
            logger.warning("No camera detected")

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

    # ── Main loop ──────────────────────────────────────────────────────────

    def run(self) -> None:
        """Pygame event loop — runs until quit."""
        self._running = True
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, lambda *_: self._request_quit())

        while self._running:
            self._handle_events()
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
                    self._request_quit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self.btn_start.is_pressed(pos):
                    self._on_start()
                elif self.btn_stop.is_pressed(pos):
                    self._on_stop()

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

        capture_config = {
            "interval_seconds": self.config.get("interval_seconds", 30),
            "photo_quality": self.config.get("photo_quality", 90),
        }
        self.engine.start(self.session, self.camera, self.storage, capture_config)
        self._capture_start_time = time.time()

        # Swap buttons
        self.btn_start.visible = False
        self.btn_stop.visible = True
        self.status_bar.update("Capturing...", 0)

    def _on_stop(self) -> None:
        """Stop the current capture session."""
        if self.engine is not None and self.engine.is_running:
            self.engine.stop()
            logger.info("Capture stopped")

        # Swap buttons back
        self.btn_stop.visible = False
        self.btn_start.visible = True
        self.status_bar.update("Stopped", self._elapsed())

    # ── Preview & status ───────────────────────────────────────────────────

    def _update_preview(self) -> None:
        """Grab the latest camera frame and push it to PreviewArea."""
        if self.camera is None:
            self.preview.update(None)
            return
        frame = self.camera.capture()
        self.preview.update(frame)

    def _update_status(self) -> None:
        """Refresh header and status bar from engine state."""
        photo_count = 0
        status_text = "Ready"
        elapsed = 0.0

        if self.engine is not None and self.engine.is_running:
            st = self.engine.get_status()
            photo_count = st.get("total_photos", 0)
            elapsed = self._elapsed()
            errors = st.get("errors", [])
            if errors:
                status_text = f"Error: {errors[-1]}"
            else:
                status_text = "Capturing..."
        elif self.engine is not None and self._capture_start_time > 0:
            # Engine was running but stopped
            st = self.engine.get_status()
            photo_count = st.get("total_photos", 0)
            elapsed = self._elapsed()
            status_text = "Stopped"

        self.header.update(self.usb_connected, photo_count)
        self.status_bar.update(status_text, elapsed)

    def _elapsed(self) -> float:
        """Seconds since capture started."""
        if self._capture_start_time > 0:
            return time.time() - self._capture_start_time
        return 0.0

    # ── Drawing ────────────────────────────────────────────────────────────

    def _draw(self) -> None:
        """Render all UI components and flip the display."""
        self.screen.fill(COLOR_BACKGROUND)
        self.header.draw(self.screen)
        self.preview.draw(self.screen)
        self.btn_start.draw(self.screen)
        self.btn_stop.draw(self.screen)
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

#!/usr/bin/env python3
"""
ui_components.py — Reusable pygame UI components for PiTimeLapse Touch.

Provides Button, Header, StatusBar, and PreviewArea classes designed for
the Waveshare/Kuman 3.5" RPi LCD (480×320) but also usable on desktop.

Color scheme: dark theme optimized for long timelapse monitoring sessions.
"""

from __future__ import annotations

import time
from typing import Optional, Tuple

import numpy as np
import pygame

# ---------------------------------------------------------------------------
# Color constants — dark theme
# ---------------------------------------------------------------------------
COLOR_BACKGROUND = (26, 26, 46)       # #1a1a2e
COLOR_HEADER = (22, 33, 62)           # #16213e
COLOR_STATUS_BAR = (15, 52, 96)       # #0f3460
COLOR_START = (78, 204, 163)          # #4ecca3
COLOR_STOP = (226, 62, 87)            # #e23e57
COLOR_TEXT = (234, 234, 234)          # #eaeaea
COLOR_TEXT_DIM = (140, 140, 160)
COLOR_USB_OK = (78, 204, 163)         # green
COLOR_USB_BAD = (226, 62, 87)         # red
COLOR_NO_CAMERA = (60, 60, 80)
COLOR_BUTTON_BORDER = (255, 255, 255, 60)
COLOR_PREVIEW_BG = (20, 20, 35)
COLOR_SETTINGS = (50, 120, 180)        # blue for settings button
COLOR_CLOSE = (160, 60, 60)            # dark red for close button
COLOR_SAVE = (78, 204, 163)            # green for save
COLOR_BACK = (120, 120, 140)           # grey for back
COLOR_STEPPER = (60, 80, 120)          # stepper +/- buttons
COLOR_FIELD_BG = (35, 35, 55)          # value field background
COLOR_TAB_ACTIVE = (15, 52, 96)        # active tab (matches status bar)
COLOR_TAB_INACTIVE = (30, 30, 50)      # inactive tab


def _darken(color: Tuple[int, ...], amount: int = 40) -> Tuple[int, ...]:
    """Return a darker version of *color* for press feedback."""
    return tuple(max(c - amount, 0) for c in color[:3])


def _lighten(color: Tuple[int, ...], amount: int = 30) -> Tuple[int, ...]:
    """Return a lighter version of *color* for hover feedback."""
    return tuple(min(c + amount, 255) for c in color[:3])


# ---------------------------------------------------------------------------
# Button
# ---------------------------------------------------------------------------
class Button:
    """Touch-friendly button with rounded corners and press feedback.

    Minimum height is enforced at 80 px for comfortable touch targets.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        color: Tuple[int, int, int] = COLOR_START,
        text_color: Tuple[int, int, int] = COLOR_TEXT,
        font_size: int = 22,
    ) -> None:
        self.rect = pygame.Rect(x, y, width, max(height, 44))
        self.text = text
        self.color = color
        self.text_color = text_color
        self.font_size = font_size
        self._font: Optional[pygame.font.Font] = None
        self._pressed = False
        self._press_time: float = 0.0
        self.visible = True

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", self.font_size, bold=True)
        return self._font

    def draw(self, surface: pygame.Surface) -> None:
        """Render the button onto *surface*."""
        if not self.visible:
            return

        # Press feedback: darken briefly
        if self._pressed and (time.time() - self._press_time < 0.15):
            fill = _darken(self.color)
        else:
            fill = self.color
            self._pressed = False

        pygame.draw.rect(surface, fill, self.rect, border_radius=12)
        # Subtle border
        pygame.draw.rect(surface, _lighten(fill, 50), self.rect, width=2, border_radius=12)

        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_pressed(self, pos: Tuple[int, int]) -> bool:
        """Return True if *pos* (from MOUSEBUTTONDOWN) hits this button."""
        if not self.visible:
            return False
        if self.rect.collidepoint(pos):
            self._pressed = True
            self._press_time = time.time()
            return True
        return False


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
class Header:
    """Top bar showing app title, USB status indicator, and photo count.

    When ``show_storage_info`` is True and a USB drive is connected the
    header also renders free space and an estimated remaining photo count.
    """

    HEIGHT = 40

    def __init__(self, screen_width: int) -> None:
        self.width = screen_width
        self._font_title: Optional[pygame.font.Font] = None
        self._font_info: Optional[pygame.font.Font] = None
        self.usb_connected = False
        self.led_detected = False
        self.photo_count = 0
        self.free_gb: float = 0.0
        self.remaining_photos: int = 0
        self.show_storage_info: bool = False

    @property
    def font_title(self) -> pygame.font.Font:
        if self._font_title is None:
            self._font_title = pygame.font.SysFont("monospace", 18, bold=True)
        return self._font_title

    @property
    def font_info(self) -> pygame.font.Font:
        if self._font_info is None:
            self._font_info = pygame.font.SysFont("monospace", 15)
        return self._font_info

    @staticmethod
    def _format_count(n: int) -> str:
        """Format large numbers compactly (e.g. 142000 → '142K')."""
        if n >= 1_000_000:
            return f"{n / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{n / 1_000:.0f}K"
        return str(n)

    def update(self, usb_connected: bool, photo_count: int,
               free_gb: float = 0.0, remaining_photos: int = 0) -> None:
        """Update header data (called each frame or on state change)."""
        self.usb_connected = usb_connected
        self.photo_count = photo_count
        self.free_gb = free_gb
        self.remaining_photos = remaining_photos

    def draw(self, surface: pygame.Surface) -> None:
        """Render the header bar."""
        pygame.draw.rect(surface, COLOR_HEADER, (0, 0, self.width, self.HEIGHT))

        # Title
        title = self.font_title.render("PiTimeLapse", True, COLOR_TEXT)
        surface.blit(title, (10, 10))

        # Right-aligned info rendered from the right edge inward
        x = self.width - 10

        # Photo count (always shown)
        count_text = f"#{self.photo_count}"
        count_surf = self.font_info.render(count_text, True, COLOR_TEXT)
        x -= count_surf.get_width()
        surface.blit(count_surf, (x, 12))

        if self.show_storage_info and self.usb_connected and self.free_gb > 0:
            # Remaining photos estimate
            rem_text = f"~{self._format_count(self.remaining_photos)} "
            rem_surf = self.font_info.render(rem_text, True, COLOR_TEXT_DIM)
            x -= rem_surf.get_width()
            surface.blit(rem_surf, (x, 12))

            # Free space
            free_text = f"{self.free_gb:.1f}G "
            free_surf = self.font_info.render(free_text, True, COLOR_TEXT_DIM)
            x -= free_surf.get_width()
            surface.blit(free_surf, (x, 12))

        # USB indicator
        usb_color = COLOR_USB_OK if self.usb_connected else COLOR_USB_BAD
        usb_char = "\u2713 " if self.usb_connected else "\u2717 "
        usb_surf = self.font_info.render(usb_char, True, usb_color)
        x -= usb_surf.get_width()
        surface.blit(usb_surf, (x, 12))

        # LED indicator (always shown next to title)
        led_color = COLOR_USB_OK if self.led_detected else COLOR_TEXT_DIM
        led_surf = self.font_info.render(" LED", True, led_color)
        surface.blit(led_surf, (10 + title.get_width(), 12))


# ---------------------------------------------------------------------------
# StatusBar
# ---------------------------------------------------------------------------
class StatusBar:
    """Bottom bar showing current status and elapsed time."""

    HEIGHT = 30

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.width = screen_width
        self.y = screen_height - self.HEIGHT
        self._font: Optional[pygame.font.Font] = None
        self.status = "Ready"
        self.elapsed: float = 0.0

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 15)
        return self._font

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        """Convert seconds to HH:MM:SS."""
        h = int(seconds) // 3600
        m = (int(seconds) % 3600) // 60
        s = int(seconds) % 60
        return f"{h:02d}:{m:02d}:{s:02d}"

    def update(self, status: str, elapsed: float) -> None:
        """Update status text and elapsed time."""
        self.status = status
        self.elapsed = elapsed

    def draw(self, surface: pygame.Surface) -> None:
        """Render the status bar."""
        pygame.draw.rect(surface, COLOR_STATUS_BAR, (0, self.y, self.width, self.HEIGHT))

        status_surf = self.font.render(f"Status: {self.status}", True, COLOR_TEXT)
        surface.blit(status_surf, (10, self.y + 6))

        elapsed_str = self._format_elapsed(self.elapsed)
        elapsed_surf = self.font.render(f"Elapsed: {elapsed_str}", True, COLOR_TEXT_DIM)
        surface.blit(elapsed_surf, (self.width - elapsed_surf.get_width() - 10, self.y + 6))


# ---------------------------------------------------------------------------
# PreviewArea
# ---------------------------------------------------------------------------
class PreviewArea:
    """Renders an OpenCV BGR frame (numpy array) onto a pygame surface.

    Scales the frame to fit the available area while preserving aspect ratio.
    Shows a "No Camera" placeholder when no frame is available.
    """

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self._frame_surface: Optional[pygame.Surface] = None
        self._placeholder_font: Optional[pygame.font.Font] = None

    @property
    def placeholder_font(self) -> pygame.font.Font:
        if self._placeholder_font is None:
            self._placeholder_font = pygame.font.SysFont("monospace", 20, bold=True)
        return self._placeholder_font

    def update(self, frame: Optional[np.ndarray]) -> None:
        """Convert a BGR numpy frame to a pygame surface scaled to fit."""
        if frame is None:
            self._frame_surface = None
            return

        # BGR → RGB
        rgb = frame[:, :, ::-1].copy()
        h, w = rgb.shape[:2]

        # Scale to fit preview area while keeping aspect ratio
        scale = min(self.rect.width / w, self.rect.height / h)
        new_w, new_h = int(w * scale), int(h * scale)

        surf = pygame.surfarray.make_surface(rgb.swapaxes(0, 1))
        self._frame_surface = pygame.transform.smoothscale(surf, (new_w, new_h))

    def draw(self, surface: pygame.Surface) -> None:
        """Render the preview (or placeholder) onto *surface*."""
        # Dark background for preview area
        pygame.draw.rect(surface, COLOR_PREVIEW_BG, self.rect)

        if self._frame_surface is not None:
            # Center the scaled frame in the preview area
            fx = self.rect.x + (self.rect.width - self._frame_surface.get_width()) // 2
            fy = self.rect.y + (self.rect.height - self._frame_surface.get_height()) // 2
            surface.blit(self._frame_surface, (fx, fy))
        else:
            # Placeholder
            text = self.placeholder_font.render("No Camera", True, COLOR_NO_CAMERA)
            text_rect = text.get_rect(center=self.rect.center)
            surface.blit(text, text_rect)

            # Draw a camera icon outline (simple rectangle + circle)
            icon_rect = pygame.Rect(0, 0, 60, 40)
            icon_rect.center = (self.rect.centerx, self.rect.centery - 30)
            pygame.draw.rect(surface, COLOR_NO_CAMERA, icon_rect, width=2, border_radius=6)
            pygame.draw.circle(surface, COLOR_NO_CAMERA, icon_rect.center, 12, 2)


class ThumbnailArea:
    """Displays the last captured photo as a thumbnail.

    Loads images from disk and caches them for performance. Only reloads when
    the path changes to minimize I/O on Raspberry Pi.
    """

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect = pygame.Rect(x, y, width, height)
        self._photo_surface: Optional[pygame.Surface] = None
        self._current_path: str = ""
        self._label_font: Optional[pygame.font.Font] = None
        self._placeholder_font: Optional[pygame.font.Font] = None

    @property
    def label_font(self) -> pygame.font.Font:
        if self._label_font is None:
            self._label_font = pygame.font.SysFont("monospace", 12, bold=True)
        return self._label_font

    @property
    def placeholder_font(self) -> pygame.font.Font:
        if self._placeholder_font is None:
            self._placeholder_font = pygame.font.SysFont("monospace", 14, bold=True)
        return self._placeholder_font

    def update_photo(self, photo_path: str) -> None:
        """Load and cache a new photo from disk. Only reloads if path changed."""
        if photo_path == self._current_path:
            return  # Already loaded
        
        self._current_path = photo_path
        
        if not photo_path:
            self._photo_surface = None
            return
        
        try:
            # Load image from disk
            img = pygame.image.load(photo_path)
            w, h = img.get_size()
            
            # Scale to fit thumbnail area (preserve aspect ratio)
            # Use regular scale (not smoothscale) for performance on Pi
            label_h = 20  # Reserve space for "Last Photo" label
            available_h = self.rect.height - label_h - 4
            scale = min((self.rect.width - 4) / w, available_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            self._photo_surface = pygame.transform.scale(img, (new_w, new_h))
        except Exception:
            # Failed to load — clear the surface
            self._photo_surface = None
            self._current_path = ""

    def draw(self, surface: pygame.Surface) -> None:
        """Render the thumbnail (or placeholder) onto *surface*."""
        # Dark background
        pygame.draw.rect(surface, COLOR_PREVIEW_BG, self.rect)
        
        # Draw label at top
        label_text = self.label_font.render("Last Photo", True, COLOR_TEXT_DIM)
        label_x = self.rect.x + (self.rect.width - label_text.get_width()) // 2
        surface.blit(label_text, (label_x, self.rect.y + 4))
        
        # Photo area starts below label
        photo_y = self.rect.y + 24
        photo_h = self.rect.height - 24
        
        if self._photo_surface is not None:
            # Center the scaled photo in the available area
            px = self.rect.x + (self.rect.width - self._photo_surface.get_width()) // 2
            py = photo_y + (photo_h - self._photo_surface.get_height()) // 2
            surface.blit(self._photo_surface, (px, py))
        else:
            # Placeholder
            placeholder = self.placeholder_font.render("No Photos", True, COLOR_NO_CAMERA)
            placeholder_rect = placeholder.get_rect(
                center=(self.rect.centerx, photo_y + photo_h // 2)
            )
            surface.blit(placeholder, placeholder_rect)


# ---------------------------------------------------------------------------
# SettingsScreen
# ---------------------------------------------------------------------------
class _SettingRow:
    """One editable setting: label + [–] value [+]."""

    def __init__(
        self,
        y: int,
        screen_w: int,
        btn_size: int,
        label: str,
        key: str,
        value: int,
        min_val: int,
        max_val: int,
        step: int,
    ) -> None:
        self.label = label
        self.key = key
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        self.step = step

        # [–]  value  [+] — right-aligned
        self.btn_minus = pygame.Rect(screen_w - 190, y, btn_size, btn_size)
        self.val_rect = pygame.Rect(screen_w - 146, y, 60, btn_size)
        self.btn_plus = pygame.Rect(screen_w - 80, y, btn_size, btn_size)
        self.label_y = y + btn_size // 2 - 8

    def handle_tap(self, pos: Tuple[int, int]) -> bool:
        """Return True if this row consumed the tap."""
        if self.btn_minus.collidepoint(pos):
            self.value = max(self.min_val, self.value - self.step)
            return True
        if self.btn_plus.collidepoint(pos):
            self.value = min(self.max_val, self.value + self.step)
            return True
        return False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        lbl = font.render(self.label, True, COLOR_TEXT)
        surface.blit(lbl, (20, self.label_y))

        # [–] button
        pygame.draw.rect(surface, COLOR_STEPPER, self.btn_minus, border_radius=6)
        minus_txt = font.render("–", True, COLOR_TEXT)
        surface.blit(minus_txt, minus_txt.get_rect(center=self.btn_minus.center))

        # Value field — show On/Off for boolean-style rows (min=0, max=1)
        pygame.draw.rect(surface, COLOR_FIELD_BG, self.val_rect, border_radius=6)
        if self.min_val == 0 and self.max_val == 1:
            display = "On" if self.value else "Off"
        else:
            display = str(self.value)
        val_txt = font.render(display, True, COLOR_TEXT)
        surface.blit(val_txt, val_txt.get_rect(center=self.val_rect.center))

        # [+] button
        pygame.draw.rect(surface, COLOR_STEPPER, self.btn_plus, border_radius=6)
        plus_txt = font.render("+", True, COLOR_TEXT)
        surface.blit(plus_txt, plus_txt.get_rect(center=self.btn_plus.center))


class SettingsScreen:
    """Full-screen settings form with tabs for 480×320 displays.

    Two tabs:
      * **Camera** — capture interval, quality, camera index, resolution.
      * **Features** — countdown, storage info, LED flash, LED warmup.

    Uses stepper controls ([–] value [+]) instead of text input —
    much easier on a small touchscreen.
    """

    TAB_HEIGHT = 34

    def __init__(self, screen_w: int, screen_h: int, config: dict,
                 led_detected: bool = False, led_port_name: str = "") -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._font: Optional[pygame.font.Font] = None
        self._font_small: Optional[pygame.font.Font] = None
        self.active_tab: int = 0  # 0 = Camera, 1 = Features, 2 = LED
        self.led_detected = led_detected
        self.led_port_name = led_port_name

        # Tab buttons — 3 tabs
        tab_w = screen_w // 3
        self.tab_rects = [
            pygame.Rect(0, 0, tab_w, self.TAB_HEIGHT),
            pygame.Rect(tab_w, 0, tab_w, self.TAB_HEIGHT),
            pygame.Rect(tab_w * 2, 0, screen_w - tab_w * 2, self.TAB_HEIGHT),
        ]
        self.tab_labels = ["Camera", "Features", "LED"]

        row_h = 36
        start_y = self.TAB_HEIGHT + 6
        btn_size = 32

        # Extract current values from config dict
        cam = config.get("camera", {})
        cap = config.get("capture", {})
        led = config.get("led", {})
        display = config.get("display", {})

        # ── Camera tab rows ──
        self.camera_rows = [
            _SettingRow(start_y, screen_w, btn_size,
                        "Interval (s)", "capture.interval_seconds",
                        int(cap.get("interval_seconds", 30)), 1, 3600, 5),
            _SettingRow(start_y + row_h, screen_w, btn_size,
                        "Quality", "capture.quality",
                        int(cap.get("quality", 90)), 1, 100, 5),
            _SettingRow(start_y + row_h * 2, screen_w, btn_size,
                        "Camera", "camera.index",
                        int(cam.get("index", 0)), 0, 9, 1),
            _SettingRow(start_y + row_h * 3, screen_w, btn_size,
                        "Width", "camera.width",
                        int(cam.get("width", 640)), 160, 1920, 160),
            _SettingRow(start_y + row_h * 4, screen_w, btn_size,
                        "Height", "camera.height",
                        int(cam.get("height", 480)), 120, 1080, 120),
        ]

        # ── Features tab rows (LED settings moved to LED tab) ──
        self.features_rows = [
            _SettingRow(start_y, screen_w, btn_size,
                        "Countdown", "display.show_countdown",
                        1 if display.get("show_countdown", True) else 0,
                        0, 1, 1),
            _SettingRow(start_y + row_h, screen_w, btn_size,
                        "Storage Info", "display.show_storage_info",
                        1 if display.get("show_storage_info", True) else 0,
                        0, 1, 1),
        ]

        # ── LED tab rows ──
        self.led_rows = [
            _SettingRow(start_y, screen_w, btn_size,
                        "LED Flash", "led.enabled",
                        1 if led.get("enabled", True) else 0, 0, 1, 1),
            _SettingRow(start_y + row_h, screen_w, btn_size,
                        "LED Warmup", "led.warmup_seconds",
                        int(led.get("warmup_seconds", 1)), 0, 5, 1),
        ]
        # Y position for LED status text (below the stepper rows)
        self._led_status_y = start_y + row_h * 2 + 10

        # Bottom buttons — positioned below the last row
        btn_w = 140
        btn_h = 48
        btn_y = screen_h - btn_h - 10
        gap = 20
        total_w = btn_w * 2 + gap
        x0 = (screen_w - total_w) // 2

        self.btn_save = pygame.Rect(x0, btn_y, btn_w, btn_h)
        self.btn_back = pygame.Rect(x0 + btn_w + gap, btn_y, btn_w, btn_h)

    @property
    def font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 18, bold=True)
        return self._font

    @property
    def font_small(self) -> pygame.font.Font:
        if self._font_small is None:
            self._font_small = pygame.font.SysFont("monospace", 14)
        return self._font_small

    def handle_tap(self, pos: Tuple[int, int]) -> Optional[str]:
        """Handle a touch/click. Returns 'save', 'back', or None."""
        # Tab switching
        for i, rect in enumerate(self.tab_rects):
            if rect.collidepoint(pos):
                self.active_tab = i
                return None

        # Active tab rows
        if self.active_tab == 0:
            rows = self.camera_rows
        elif self.active_tab == 1:
            rows = self.features_rows
        else:
            rows = self.led_rows
        for row in rows:
            row.handle_tap(pos)

        if self.btn_save.collidepoint(pos):
            return "save"
        if self.btn_back.collidepoint(pos):
            return "back"
        return None

    def get_values(self) -> dict:
        """Return current settings as a nested config dict."""
        flat = {}
        for row in self.camera_rows + self.features_rows + self.led_rows:
            flat[row.key] = row.value
        return {
            "camera": {
                "mode": "opencv",
                "index": flat.get("camera.index", 0),
                "width": flat.get("camera.width", 640),
                "height": flat.get("camera.height", 480),
            },
            "capture": {
                "interval_seconds": flat.get("capture.interval_seconds", 30),
                "quality": flat.get("capture.quality", 90),
            },
            "preview": {"fps": 6},
            "storage": {"fallback_path": "./data"},
            "led": {
                "enabled": bool(flat.get("led.enabled", 1)),
                "warmup_seconds": flat.get("led.warmup_seconds", 1),
            },
            "display": {
                "show_countdown": bool(flat.get("display.show_countdown", 1)),
                "show_storage_info": bool(flat.get("display.show_storage_info", 1)),
            },
        }

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BACKGROUND)

        # ── Tab bar ──
        for i, (rect, label) in enumerate(zip(self.tab_rects, self.tab_labels)):
            color = COLOR_TAB_ACTIVE if i == self.active_tab else COLOR_TAB_INACTIVE
            text_color = COLOR_TEXT if i == self.active_tab else COLOR_TEXT_DIM
            pygame.draw.rect(surface, color, rect)
            # Highlight strip under active tab
            if i == self.active_tab:
                pygame.draw.line(surface, COLOR_START,
                                 (rect.left + 4, rect.bottom - 2),
                                 (rect.right - 4, rect.bottom - 2), 3)
            tab_txt = self.font.render(label, True, text_color)
            surface.blit(tab_txt, tab_txt.get_rect(center=rect.center))

        # ── Setting rows for active tab ──
        if self.active_tab == 0:
            rows = self.camera_rows
        elif self.active_tab == 1:
            rows = self.features_rows
        else:
            rows = self.led_rows
        for row in rows:
            row.draw(surface, self.font)

        # ── LED status text (only on LED tab) ──
        if self.active_tab == 2:
            if self.led_detected:
                status_text = f"\u2713 Detected on {self.led_port_name}"
                status_color = COLOR_USB_OK
            else:
                status_text = "\u2717 Not detected"
                status_color = COLOR_TEXT_DIM
            status_surf = self.font_small.render(status_text, True, status_color)
            surface.blit(status_surf, (14, self._led_status_y))
            if not self.led_detected:
                hint_surf = self.font_small.render("(install uhubctl)",
                                                   True, COLOR_TEXT_DIM)
                surface.blit(hint_surf, (14, self._led_status_y + 18))

        # ── Save button ──
        pygame.draw.rect(surface, COLOR_SAVE, self.btn_save, border_radius=10)
        save_txt = self.font.render("SAVE", True, COLOR_TEXT)
        surface.blit(save_txt, save_txt.get_rect(center=self.btn_save.center))

        # ── Back button ──
        pygame.draw.rect(surface, COLOR_BACK, self.btn_back, border_radius=10)
        back_txt = self.font.render("BACK", True, COLOR_TEXT)
        surface.blit(back_txt, back_txt.get_rect(center=self.btn_back.center))

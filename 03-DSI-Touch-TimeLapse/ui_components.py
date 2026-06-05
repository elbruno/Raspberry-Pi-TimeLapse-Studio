#!/usr/bin/env python3
"""
ui_components.py — Reusable pygame UI components for PiTimeLapse Touch.

Provides Button, Header, StatusBar, and PreviewArea classes designed for
the Waveshare/Kuman 3.5" RPi LCD (480×320) but also usable on desktop.

Color scheme: dark theme optimized for long timelapse monitoring sessions.
"""

from __future__ import annotations

import copy
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
COLOR_TEST = (125, 96, 196)            # diagnostic action buttons
COLOR_PANEL_BG = (31, 34, 58)
COLOR_PANEL_BORDER = (95, 108, 142)
COLOR_PANEL_TITLE_BG = (38, 63, 102)
COLOR_PANEL_ACCENT = (87, 196, 170)


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
        self.relay_2_detected = False
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

        # Relay indicators (always shown next to title)
        led_color = COLOR_USB_OK if self.led_detected else COLOR_TEXT_DIM
        led_surf = self.font_info.render(" R1", True, led_color)
        surface.blit(led_surf, (10 + title.get_width(), 12))
        relay2_color = COLOR_USB_OK if self.relay_2_detected else COLOR_TEXT_DIM
        relay2_surf = self.font_info.render(" R2", True, relay2_color)
        surface.blit(relay2_surf, (10 + title.get_width() + led_surf.get_width(), 12))


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

                Four tabs:
      * **Camera** — capture interval, quality, camera index, resolution.
            * **Display** — app window size, centering, fullscreen, header toggles.
            * **LED** — LED settings + LED diagnostics.
            * **Buttons** — physical button mapping + diagnostics.

    Uses stepper controls ([–] value [+]) instead of text input —
    much easier on a small touchscreen.
    """

    TAB_HEIGHT = 34

    PANEL_MARGIN = 12
    PANEL_GAP = 10

    @staticmethod
    def _build_window_size_options(
        max_size: Tuple[int, int],
        current_size: Tuple[int, int],
    ) -> tuple[list[tuple[int, int]], int]:
        """Return 16:9 window presets up to the current display resolution."""
        max_w, max_h = max_size
        # Some SDL backends report current window size instead of full desktop size
        # when running windowed. Keep at least a practical baseline so the user can
        # still cycle presets (e.g., 640x360 -> 800x450 on DSI screens).
        max_w = max(max_w, 800)
        max_h = max(max_h, 450)
        current_w, current_h = current_size

        preset_candidates = [
            (640, 360),
            (800, 450),
            (960, 540),
            (1024, 576),
            (1280, 720),
            (1600, 900),
            (1920, 1080),
            (2560, 1440),
        ]
        options = [(w, h) for w, h in preset_candidates if w <= max_w and h <= max_h]

        if not options:
            fallback_w = max(320, min(max_w, current_w))
            fallback_w -= fallback_w % 16
            fallback_h = max(180, (fallback_w * 9) // 16)
            if fallback_h > max_h:
                fallback_h = max(180, min(max_h, current_h))
                fallback_h -= fallback_h % 9
                fallback_w = max(320, (fallback_h * 16) // 9)
            options = [(fallback_w, fallback_h)]

        selected = min(
            range(len(options)),
            key=lambda idx: abs(options[idx][0] - current_w) + abs(options[idx][1] - current_h),
        )
        return options, selected

    def __init__(self, screen_w: int, screen_h: int, config: dict,
                 led_detected: bool = False, led_port_name: str = "",
                 relay_2_detected: bool = False, relay_2_port_name: str = "",
                 camera_options: Optional[list[tuple[int, str]]] = None,
                 grove_buttons_detected: bool = False,
                 max_display_size: Optional[Tuple[int, int]] = None) -> None:
        self.screen_w = screen_w
        self.screen_h = screen_h
        self._font: Optional[pygame.font.Font] = None
        self._font_small: Optional[pygame.font.Font] = None
        self.active_tab: int = 0  # 0=Camera, 1=Display, 2=LED, 3=Buttons
        self.led_detected = led_detected
        self.led_port_name = led_port_name
        self.relay_2_detected = relay_2_detected
        self.relay_2_port_name = relay_2_port_name
        self.grove_buttons_detected = grove_buttons_detected
        self.button_test_active = False
        self.button_test_counts = {"button1": 0, "button2": 0}
        self.button_flash_until = {"button1": 0.0, "button2": 0.0}
        self.last_button_pressed = ""
        self.hardware_message = ""
        self.hardware_message_color = COLOR_TEXT_DIM
        self.led_test_running = False
        self.led_test_flash_until = 0.0
        self.relay_2_test_running = False
        self.relay_2_test_flash_until = 0.0
        self.camera_detect_running = False
        self.led_detect_running = False
        self.relay_2_detect_running = False
        self.camera_preview_frame: Optional[pygame.Surface] = None
        self.camera_preview_timestamp: float = 0.0

        # Tab buttons — 4 tabs
        tab_w = screen_w // 4
        self.tab_rects = [
            pygame.Rect(0, 0, tab_w, self.TAB_HEIGHT),
            pygame.Rect(tab_w, 0, tab_w, self.TAB_HEIGHT),
            pygame.Rect(tab_w * 2, 0, tab_w, self.TAB_HEIGHT),
            pygame.Rect(tab_w * 3, 0, screen_w - tab_w * 3, self.TAB_HEIGHT),
        ]
        self.tab_labels = ["Camera", "Display", "LED", "Buttons"]

        row_h = 48
        start_y = self.TAB_HEIGHT + 6
        btn_size = 32

        # Extract current values from config dict
        cam = config.get("camera", {})
        cap = config.get("capture", {})
        led = config.get("led", {})
        display = config.get("display", {})
        display_max = max_display_size or (screen_w, screen_h)

        self.window_size_options, self._window_size_selected = self._build_window_size_options(
            display_max,
            (
                int(display.get("window_width", screen_w)),
                int(display.get("window_height", screen_h)),
            ),
        )

        # Available cameras for combo-style selector, e.g. [(1, "LifeCam"), ...]
        self.camera_options: list[tuple[int, str]] = sorted(
            camera_options or [],
            key=lambda item: item[0],
        )

        configured_index = int(cam.get("index", 0))
        if self.camera_options:
            selected = 0
            for i, (cam_idx, _) in enumerate(self.camera_options):
                if cam_idx == configured_index:
                    selected = i
                    break
            self._camera_selected = selected
        else:
            # Fallback when no camera is detected: preserve manual index value
            self._camera_selected = 0
            self.camera_options = [(configured_index, "Manual idx")]

        grove_button = config.get("grove_button", {})
        relay = config.get("grove_relay", {})
        relay_2 = config.get("grove_relay_2", {})
        self._start_stop_options: list[tuple[str, str]] = [
            ("button1", "Btn1"),
            ("button2", "Btn2"),
        ]
        configured_start_stop = str(grove_button.get("start_stop_button", "button1"))
        self._start_stop_selected = 0
        for idx_opt, (value, _) in enumerate(self._start_stop_options):
            if value == configured_start_stop:
                self._start_stop_selected = idx_opt
                break

        # Camera combo row geometry (placed below Interval/Quality rows).
        camera_selector_y = start_y + row_h * 2
        self.camera_label_y = camera_selector_y + btn_size // 2 - 8
        self.camera_btn_prev = pygame.Rect(screen_w - 190, camera_selector_y, btn_size, btn_size)
        self.camera_val_rect = pygame.Rect(screen_w - 146, camera_selector_y, 100, btn_size)
        self.camera_btn_next = pygame.Rect(screen_w - 40, camera_selector_y, btn_size, btn_size)

        self.window_size_label_y = start_y + row_h * 2 + btn_size // 2 - 8
        self.window_size_btn_prev = pygame.Rect(screen_w - 190, start_y + row_h * 2, btn_size, btn_size)
        self.window_size_val_rect = pygame.Rect(screen_w - 146, start_y + row_h * 2, 100, btn_size)
        self.window_size_btn_next = pygame.Rect(screen_w - 40, start_y + row_h * 2, btn_size, btn_size)

        self.source_mode_options: list[tuple[str, str]] = [
            ("daemon_primary", "A"),
            ("direct_primary", "B"),
            ("direct_only", "D"),
        ]
        configured_source_mode = str(cam.get("source_mode", "daemon_primary"))
        self._source_mode_selected = 0
        for idx_opt, (value, _) in enumerate(self.source_mode_options):
            if value == configured_source_mode:
                self._source_mode_selected = idx_opt
                break

        source_mode_y = start_y + row_h * 3
        self.source_mode_label_y = source_mode_y + btn_size // 2 - 8
        self.source_mode_btn_prev = pygame.Rect(screen_w - 190, source_mode_y, btn_size, btn_size)
        self.source_mode_val_rect = pygame.Rect(screen_w - 146, source_mode_y, 100, btn_size)
        self.source_mode_btn_next = pygame.Rect(screen_w - 40, source_mode_y, btn_size, btn_size)

        self.start_stop_label_y = start_y + row_h + btn_size // 2 - 8
        self.start_stop_btn_prev = pygame.Rect(screen_w - 190, start_y + row_h, btn_size, btn_size)
        self.start_stop_val_rect = pygame.Rect(screen_w - 146, start_y + row_h, 100, btn_size)
        self.start_stop_btn_next = pygame.Rect(screen_w - 40, start_y + row_h, btn_size, btn_size)

        # ── Camera tab rows (full width, will be drawn on left) ──
        self.camera_rows = [
            _SettingRow(start_y, screen_w, btn_size,
                        "Interval (s)", "capture.interval_seconds",
                        int(cap.get("interval_seconds", 30)), 1, 3600, 5),
            _SettingRow(start_y + row_h, screen_w, btn_size,
                        "Quality", "capture.quality",
                        int(cap.get("quality", 90)), 1, 100, 5),
            _SettingRow(start_y + row_h * 2, screen_w, btn_size,
                        "Cam Index", "camera.index",
                        int(cam.get("index", 0)), 0, 9, 1),
        ]
        
        # Track last camera index for validation callback
        self._last_camera_index = int(cam.get("index", 0))

        # ── Display tab rows ──
        self.display_rows = [
            _SettingRow(start_y, screen_w, btn_size,
                        "Countdown", "display.show_countdown",
                        1 if display.get("show_countdown", True) else 0,
                        0, 1, 1),
            _SettingRow(start_y + row_h, screen_w, btn_size,
                        "Storage Info", "display.show_storage_info",
                        1 if display.get("show_storage_info", True) else 0,
                        0, 1, 1),
            _SettingRow(start_y + row_h * 3, screen_w, btn_size,
                        "Center Window", "display.center_window",
                        1 if display.get("center_window", True) else 0,
                        0, 1, 1),
            _SettingRow(start_y + row_h * 4, screen_w, btn_size,
                        "Fullscreen", "display.fullscreen",
                        1 if display.get("fullscreen", False) else 0,
                        0, 1, 1),
        ]

        # ── LED tab rows (full width, will be drawn on left) ──
        self.led_rows = [
            _SettingRow(start_y, screen_w, btn_size,
                        "Relay 1 Pin", "grove_relay.pin",
                        int(relay.get("pin", 26)), 0, 27, 1),
            _SettingRow(start_y + row_h, screen_w, btn_size,
                        "R1 Active High", "grove_relay.active_high",
                        1 if relay.get("active_high", True) else 0, 0, 1, 1),
            _SettingRow(start_y + row_h * 2, screen_w, btn_size,
                        "Enable Relay 1", "grove_relay.enabled",
                        1 if relay.get("enabled", True) else 0, 0, 1, 1),
            _SettingRow(start_y + row_h * 3, screen_w, btn_size,
                        "Relay 2 Pin", "grove_relay_2.pin",
                        int(relay_2.get("pin", 24)), 0, 27, 1),
            _SettingRow(start_y + row_h * 4, screen_w, btn_size,
                        "R2 Active High", "grove_relay_2.active_high",
                        1 if relay_2.get("active_high", True) else 0, 0, 1, 1),
            _SettingRow(start_y + row_h * 5, screen_w, btn_size,
                        "Enable Relay 2", "grove_relay_2.enabled",
                        1 if relay_2.get("enabled", True) else 0, 0, 1, 1),
            _SettingRow(start_y + row_h * 6, screen_w, btn_size,
                        "Enable Relays", "led.enabled",
                        1 if led.get("enabled", True) else 0, 0, 1, 1),
            _SettingRow(start_y + row_h * 7, screen_w, btn_size,
                        "Warmup (s)", "led.warmup_seconds",
                        int(led.get("warmup_seconds", 1)), 0, 30, 1),
        ]

        # ── Buttons tab rows ──
        self.button_rows = []

        # Diagnostic buttons and status blocks
        self.btn_camera_detect = pygame.Rect(20, start_y + row_h * 3 + 2, 160, 36)
        relay_test_w = 126
        relay_detect_w = 96
        relay_btn_gap = 10
        relay_detect_x = 20 + relay_test_w + relay_btn_gap

        self.btn_led_test = pygame.Rect(20, start_y + row_h * 2, relay_test_w, 36)
        self.btn_led_detect = pygame.Rect(relay_detect_x, start_y + row_h * 2, relay_detect_w, 36)
        self.btn_relay_2_test = pygame.Rect(20, start_y + row_h * 3, relay_test_w, 36)
        self.btn_relay_2_detect = pygame.Rect(relay_detect_x, start_y + row_h * 3, relay_detect_w, 36)
        self.btn_button_test = pygame.Rect(20, start_y + row_h * 2 + 8, screen_w - 40, 40)
        self._led_status_y = start_y + row_h * 4 + 10
        self._button_status_y = start_y + row_h * 3 + 10
        self._camera_status_y = start_y + row_h * 4

        # Bottom buttons — positioned below the last row
        btn_w = 140
        btn_h = 48
        btn_y = screen_h - btn_h - 10
        gap = 20
        total_w = btn_w * 2 + gap
        x0 = (screen_w - total_w) // 2

        self.btn_save = pygame.Rect(x0, btn_y, btn_w, btn_h)
        self.btn_back = pygame.Rect(x0 + btn_w + gap, btn_y, btn_w, btn_h)

        # Camera tab two-panel layout
        self.camera_general_rect = pygame.Rect(0, 0, 0, 0)
        self.camera_preview_rect = pygame.Rect(0, 0, 0, 0)
        self.camera_list_pos: Tuple[int, int] = (0, 0)
        self._layout_camera_tab_sections(start_y, row_h)

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
            if self.btn_camera_detect.collidepoint(pos):
                return "detect_camera"
            if self.source_mode_btn_prev.collidepoint(pos):
                self._source_mode_selected = (self._source_mode_selected - 1) % len(self.source_mode_options)
                return None
            if self.source_mode_btn_next.collidepoint(pos):
                self._source_mode_selected = (self._source_mode_selected + 1) % len(self.source_mode_options)
                return None
            rows = self.camera_rows
        elif self.active_tab == 1:
            if self.window_size_btn_prev.collidepoint(pos):
                self._window_size_selected = (self._window_size_selected - 1) % len(self.window_size_options)
                return None
            if self.window_size_btn_next.collidepoint(pos):
                self._window_size_selected = (self._window_size_selected + 1) % len(self.window_size_options)
                return None
            rows = self.display_rows
        elif self.active_tab == 2:
            if self.btn_led_test.collidepoint(pos):
                self.led_test_flash_until = time.time() + 0.18
                return "test_led"
            if self.btn_led_detect.collidepoint(pos):
                return "detect_led"
            if self.btn_relay_2_test.collidepoint(pos):
                self.relay_2_test_flash_until = time.time() + 0.18
                return "test_relay_2"
            if self.btn_relay_2_detect.collidepoint(pos):
                return "detect_relay_2"
            rows = self.led_rows
        else:
            if self.start_stop_btn_prev.collidepoint(pos):
                self._start_stop_selected = (self._start_stop_selected - 1) % len(self._start_stop_options)
                return None
            if self.start_stop_btn_next.collidepoint(pos):
                self._start_stop_selected = (self._start_stop_selected + 1) % len(self._start_stop_options)
                return None
            if self.btn_button_test.collidepoint(pos):
                self.button_test_active = not self.button_test_active
                if self.button_test_active:
                    self.set_hardware_message("Button test enabled — press the physical buttons", True)
                else:
                    self.set_hardware_message("Button test stopped", False)
                return None
            rows = self.button_rows
        for row in rows:
            row.handle_tap(pos)

        if self.btn_save.collidepoint(pos):
            return "save"
        if self.btn_back.collidepoint(pos):
            return "back"
        return None

    def set_hardware_message(self, message: str, success: bool) -> None:
        """Update the diagnostic status message shown on the hardware tab."""
        self.hardware_message = message
        self.hardware_message_color = COLOR_USB_OK if success else COLOR_TEXT_DIM

    def register_hardware_button(self, button_name: str) -> None:
        """Record a physical button press while the settings screen is open."""
        if not self.button_test_active:
            return

        if button_name not in self.button_test_counts:
            return

        self.button_test_counts[button_name] += 1
        self.button_flash_until[button_name] = time.time() + 1.0
        self.last_button_pressed = button_name
        self.set_hardware_message(f"Detected {button_name}", True)

    def set_led_test_running(self, running: bool) -> None:
        """Update visual state for the LED test action button."""
        self.led_test_running = running

    def set_camera_detect_running(self, running: bool) -> None:
        """Update visual state for the camera detect action button."""
        self.camera_detect_running = running

    def set_led_detect_running(self, running: bool) -> None:
        """Update visual state for the LED detect action button."""
        self.led_detect_running = running

    def set_relay_2_test_running(self, running: bool) -> None:
        """Update visual state for Relay #2 test button."""
        self.relay_2_test_running = running

    def set_relay_2_detect_running(self, running: bool) -> None:
        """Update visual state for Relay #2 detect button."""
        self.relay_2_detect_running = running

    def set_camera_preview_frame(self, frame: Optional[pygame.Surface]) -> None:
        """Update the camera preview frame displayed on the Camera tab."""
        self.camera_preview_frame = frame
        self.camera_preview_timestamp = time.time()

    def _layout_camera_tab_sections(self, start_y: int, row_h: int) -> None:
        """Compute two-panel layout for Camera tab and reflow row controls."""
        content_top = start_y
        content_bottom = self.btn_save.y - 10
        content_h = max(140, content_bottom - content_top)

        margin = self.PANEL_MARGIN
        gap = self.PANEL_GAP
        available_w = self.screen_w - (margin * 2)

        # Camera preview is 30% of screen width, general config gets the rest
        right_w = int(self.screen_w * 0.30)
        right_w = max(120, right_w)  # Minimum viable preview width
        left_w = available_w - right_w - gap

        general_x = margin
        preview_x = general_x + left_w + gap

        self.camera_general_rect = pygame.Rect(general_x, content_top, left_w, content_h)
        camera_preview_panel_rect = pygame.Rect(preview_x, content_top, right_w, content_h)

        # Reflow interval/quality steppers to fit the general panel.
        stepper_size = 30
        plus_x = self.camera_general_rect.right - 12 - stepper_size
        val_w = 52
        val_x = plus_x - 6 - val_w
        minus_x = val_x - 6 - stepper_size
        for row in self.camera_rows:
            row.btn_minus = pygame.Rect(minus_x, row.btn_minus.y, stepper_size, stepper_size)
            row.val_rect = pygame.Rect(val_x, row.val_rect.y, val_w, stepper_size)
            row.btn_plus = pygame.Rect(plus_x, row.btn_plus.y, stepper_size, stepper_size)

        # Section 2: detect button + preview + list.
        detect_x = camera_preview_panel_rect.x + 12
        detect_y = camera_preview_panel_rect.y + 14
        detect_w = min(160, camera_preview_panel_rect.width - 24)
        self.btn_camera_detect = pygame.Rect(detect_x, detect_y, detect_w, 36)

        preview_x = camera_preview_panel_rect.x + 12
        preview_y = self.btn_camera_detect.bottom + 8
        preview_w = camera_preview_panel_rect.width - 24
        preview_h = max(60, camera_preview_panel_rect.height - 36 - 8 - 100)
        self.camera_preview_rect = pygame.Rect(preview_x, preview_y, preview_w, preview_h)
        self.camera_list_pos = (preview_x, self.camera_preview_rect.bottom + 6)

    def get_values(self, base_config: Optional[dict] = None) -> dict:
        """Return current settings as a nested config dict."""
        flat = {}
        for row in self.camera_rows + self.display_rows + self.led_rows + self.button_rows:
            flat[row.key] = row.value

        config = copy.deepcopy(base_config or {})
        config.setdefault("camera", {})
        config["camera"].setdefault("daemon", config.get("camera", {}).get("daemon", {}))
        config.setdefault("capture", {})
        config.setdefault("preview", {"fps": 6})
        config.setdefault("storage", {"fallback_path": "./data"})
        config.setdefault("led", {})
        config.setdefault("display", {})
        config.setdefault("grove_button", config.get("grove_button", {}))
        config.setdefault("grove_relay", config.get("grove_relay", {}))
        config.setdefault("grove_relay_2", config.get("grove_relay_2", {}))

        selected_camera_idx = flat.get("camera.index", 0)

        config["camera"].update({
            "mode": "opencv",
            "source_mode": self.source_mode_options[self._source_mode_selected][0],
            "index": int(selected_camera_idx),
            "width": flat.get("camera.width", 640),
            "height": flat.get("camera.height", 480),
        })
        config["capture"].update({
            "interval_seconds": flat.get("capture.interval_seconds", 30),
            "quality": flat.get("capture.quality", 90),
        })
        config["led"].update({
            "enabled": bool(flat.get("led.enabled", 1)),
            "warmup_seconds": flat.get("led.warmup_seconds", 1),
            "pre_capture_lead_seconds": config["led"].get("pre_capture_lead_seconds", 0.0),
        })
        window_width, window_height = self.window_size_options[self._window_size_selected]
        config["display"].update({
            "show_countdown": bool(flat.get("display.show_countdown", 1)),
            "show_storage_info": bool(flat.get("display.show_storage_info", 1)),
            "window_width": window_width,
            "window_height": window_height,
            "center_window": bool(flat.get("display.center_window", 1)),
            "fullscreen": bool(flat.get("display.fullscreen", 0)),
        })
        config["grove_button"].update({
            "start_stop_button": self._start_stop_options[self._start_stop_selected][0],
        })
        config["grove_relay"].update({
            "enabled": bool(flat.get("grove_relay.enabled", 1)),
            "pin": int(flat.get("grove_relay.pin", 26)),
            "active_high": bool(flat.get("grove_relay.active_high", 1)),
        })
        config["grove_relay_2"].update({
            "enabled": bool(flat.get("grove_relay_2.enabled", 1)),
            "pin": int(flat.get("grove_relay_2.pin", 24)),
            "active_high": bool(flat.get("grove_relay_2.active_high", 1)),
        })

        return config

    def _draw_action_button(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        label: str,
        color: Tuple[int, int, int],
    ) -> None:
        """Render a wide diagnostics button."""
        pygame.draw.rect(surface, color, rect, border_radius=10)
        pygame.draw.rect(surface, _lighten(color, 30), rect, width=2, border_radius=10)
        text = self.font.render(label, True, COLOR_TEXT)
        surface.blit(text, text.get_rect(center=rect.center))

    def _draw_button_state(
        self,
        surface: pygame.Surface,
        label: str,
        key: str,
        x: int,
        y: int,
    ) -> None:
        """Render a compact status tile for a physical button."""
        active = time.time() < self.button_flash_until.get(key, 0.0)
        tile = pygame.Rect(x, y, 140, 54)
        color = COLOR_USB_OK if active else COLOR_FIELD_BG
        pygame.draw.rect(surface, color, tile, border_radius=8)
        pygame.draw.rect(surface, _lighten(color, 25), tile, width=2, border_radius=8)

        title = self.font_small.render(label, True, COLOR_TEXT)
        count = self.font.render(str(self.button_test_counts.get(key, 0)), True, COLOR_TEXT)
        surface.blit(title, (tile.x + 10, tile.y + 8))
        surface.blit(count, (tile.x + 10, tile.y + 24))

    def _draw_section_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        title: str,
        title_y: int,
    ) -> None:
        """Render a card-like section container with an accent title badge."""
        shadow = rect.move(0, 2)
        pygame.draw.rect(surface, _darken(COLOR_PANEL_BG, 10), shadow, border_radius=10)
        pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=2, border_radius=10)

        chip_text = self.font_small.render(title, True, COLOR_TEXT)
        chip_w = chip_text.get_width() + 18
        chip_h = 18
        chip_rect = pygame.Rect(rect.x + 10, title_y, chip_w, chip_h)
        pygame.draw.rect(surface, COLOR_PANEL_TITLE_BG, chip_rect, border_radius=8)
        pygame.draw.rect(surface, _lighten(COLOR_PANEL_TITLE_BG, 25), chip_rect, width=1, border_radius=8)
        surface.blit(chip_text, chip_text.get_rect(center=chip_rect.center))

        pygame.draw.line(
            surface,
            COLOR_PANEL_ACCENT,
            (rect.x + 10, rect.y + 10),
            (rect.x + min(70, rect.width - 10), rect.y + 10),
            2,
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(COLOR_BACKGROUND)

        # Local layout constants used by tab-specific custom sections.
        # Keep these in sync with __init__ geometry baselines.
        row_h = 48
        start_y = self.TAB_HEIGHT + 6
        screen_w = self.screen_w

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
        if self.active_tab == 1:
            rows = self.display_rows
        elif self.active_tab == 2:
            rows = self.led_rows
        else:
            rows = self.button_rows
        for row in rows:
            row.draw(surface, self.font)

        # Camera combo-like selector (Camera tab)
        if self.active_tab == 0:
            # Section containers
            preview_panel_rect = pygame.Rect(
                self.camera_preview_rect.x - 12,
                self.camera_general_rect.y,
                self.camera_preview_rect.width + 24,
                self.camera_general_rect.height,
            )
            title1_y = max(self.TAB_HEIGHT + 2, self.camera_general_rect.y - 14)
            title2_y = max(self.TAB_HEIGHT + 2, preview_panel_rect.y - 14)
            self._draw_section_panel(surface, self.camera_general_rect, "General Config", title1_y)
            self._draw_section_panel(surface, preview_panel_rect, "Camera Preview & Detect", title2_y)

            divider_x = (self.camera_general_rect.right + preview_panel_rect.x) // 2
            pygame.draw.line(
                surface,
                _darken(COLOR_PANEL_BORDER, 10),
                (divider_x, self.camera_general_rect.y + 14),
                (divider_x, self.camera_general_rect.bottom - 14),
                1,
            )

            # Draw camera config rows after panel backgrounds so rows stay visible.
            for row in self.camera_rows:
                row.draw(surface, self.font)

            source_lbl = self.font.render("Source Mode", True, COLOR_TEXT)
            surface.blit(source_lbl, (20, self.source_mode_label_y))

            pygame.draw.rect(surface, COLOR_STEPPER, self.source_mode_btn_prev, border_radius=6)
            source_prev_txt = self.font.render("<", True, COLOR_TEXT)
            surface.blit(source_prev_txt, source_prev_txt.get_rect(center=self.source_mode_btn_prev.center))

            pygame.draw.rect(surface, COLOR_FIELD_BG, self.source_mode_val_rect, border_radius=6)
            source_mode_value = self.source_mode_options[self._source_mode_selected][0]
            if source_mode_value == "daemon_primary":
                source_mode_label = "A: Daemon"
            elif source_mode_value == "direct_primary":
                source_mode_label = "B: Direct"
            else:
                source_mode_label = "Direct only"
            source_mode_txt = self.font_small.render(source_mode_label, True, COLOR_TEXT)
            surface.blit(source_mode_txt, source_mode_txt.get_rect(center=self.source_mode_val_rect.center))

            pygame.draw.rect(surface, COLOR_STEPPER, self.source_mode_btn_next, border_radius=6)
            source_next_txt = self.font.render(">", True, COLOR_TEXT)
            surface.blit(source_next_txt, source_next_txt.get_rect(center=self.source_mode_btn_next.center))

            # Detect camera button
            camera_detect_color = COLOR_TEST
            if self.camera_detect_running:
                camera_detect_color = COLOR_STOP
            self._draw_action_button(surface, self.btn_camera_detect, "DETECT", camera_detect_color)

            # Large camera preview area in section 2
            preview_rect = self.camera_preview_rect
            pygame.draw.rect(surface, COLOR_PREVIEW_BG, preview_rect, border_radius=8)
            pygame.draw.rect(surface, COLOR_TEXT_DIM, preview_rect, width=2, border_radius=8)
            
            if self.camera_preview_frame is not None:
                # Scale frame to fit preview area
                frame_scaled = pygame.transform.scale(
                    self.camera_preview_frame,
                    (max(1, preview_rect.width - 4), max(1, preview_rect.height - 4)),
                )
                surface.blit(frame_scaled, (preview_rect.x + 2, preview_rect.y + 2))
            else:
                # Show placeholder text
                placeholder = self.font_small.render("Tap DETECT to scan", True, COLOR_TEXT_DIM)
                surface.blit(placeholder, placeholder.get_rect(center=preview_rect.center))
            
            # Available cameras list below preview
            preview_x, list_y = self.camera_list_pos
            if self.camera_options:
                list_bg = pygame.Rect(preview_x - 4, list_y - 2, preview_rect.width + 8, 38)
                pygame.draw.rect(surface, _darken(COLOR_PANEL_BG, 4), list_bg, border_radius=6)
                cameras_text = self.font_small.render(f"Available ({len(self.camera_options)}):", True, COLOR_TEXT)
                surface.blit(cameras_text, (preview_x, list_y))
                for i, (idx, name) in enumerate(self.camera_options[:2]):  # Show first 2
                    short_name = name[:16] if len(name) > 16 else name
                    color = COLOR_USB_OK if i == self._camera_selected else COLOR_TEXT_DIM
                    cam_item = self.font_small.render(f"[{idx}] {short_name}", True, color)
                    surface.blit(cam_item, (preview_x + 8, list_y + 14 + i * 13))

            if self.hardware_message:
                msg = self.font_small.render(self.hardware_message[:52], True, self.hardware_message_color)
                message_y = min(list_y + 44, self.btn_save.y - 20)
                surface.blit(msg, (preview_x, message_y))

        if self.active_tab == 1:
            size_lbl = self.font.render("App Size", True, COLOR_TEXT)
            surface.blit(size_lbl, (20, self.window_size_label_y))

            pygame.draw.rect(surface, COLOR_STEPPER, self.window_size_btn_prev, border_radius=6)
            prev_txt = self.font.render("<", True, COLOR_TEXT)
            surface.blit(prev_txt, prev_txt.get_rect(center=self.window_size_btn_prev.center))

            pygame.draw.rect(surface, COLOR_FIELD_BG, self.window_size_val_rect, border_radius=6)
            window_width, window_height = self.window_size_options[self._window_size_selected]
            size_txt = self.font_small.render(f"{window_width}x{window_height}", True, COLOR_TEXT)
            surface.blit(size_txt, size_txt.get_rect(center=self.window_size_val_rect.center))

            pygame.draw.rect(surface, COLOR_STEPPER, self.window_size_btn_next, border_radius=6)
            next_txt = self.font.render(">", True, COLOR_TEXT)
            surface.blit(next_txt, next_txt.get_rect(center=self.window_size_btn_next.center))

        # ── LED diagnostics (only on LED tab) ──
        if self.active_tab == 2:
            # Test and Detect buttons side by side at top
            led_test_color = COLOR_TEST
            if self.led_test_running:
                led_test_color = COLOR_STOP
            elif time.time() < self.led_test_flash_until:
                led_test_color = _lighten(COLOR_TEST, 35)
            self._draw_action_button(surface, self.btn_led_test, "TEST R1", led_test_color)

            # Detect LED button
            led_detect_color = COLOR_TEST
            if self.led_detect_running:
                led_detect_color = COLOR_STOP
            self._draw_action_button(surface, self.btn_led_detect, "DETECT", led_detect_color)

            relay_2_test_color = COLOR_TEST
            if self.relay_2_test_running:
                relay_2_test_color = COLOR_STOP
            elif time.time() < self.relay_2_test_flash_until:
                relay_2_test_color = _lighten(COLOR_TEST, 35)
            self._draw_action_button(surface, self.btn_relay_2_test, "TEST R2", relay_2_test_color)

            relay_2_detect_color = COLOR_TEST
            if self.relay_2_detect_running:
                relay_2_detect_color = COLOR_STOP
            self._draw_action_button(surface, self.btn_relay_2_detect, "DETECT R2", relay_2_detect_color)

            # Status display on right side (below palette)
            status_x = screen_w - 220
            status_y = start_y + row_h * 4
            
            r1_status = "✓" if self.led_detected else "✗"
            r2_status = "✓" if self.relay_2_detected else "✗"
            r1_color = COLOR_USB_OK if self.led_detected else COLOR_TEXT_DIM
            r2_color = COLOR_USB_OK if self.relay_2_detected else COLOR_TEXT_DIM

            r1_surf = self.font_small.render(f"R1 {r1_status} {self.led_port_name or 'GPIO'}", True, r1_color)
            r2_surf = self.font_small.render(f"R2 {r2_status} {self.relay_2_port_name or 'GPIO'}", True, r2_color)
            surface.blit(r1_surf, (status_x, status_y))
            surface.blit(r2_surf, (status_x, status_y + 18))

            if self.hardware_message:
                msg_surf = self.font_small.render(self.hardware_message[:46], True, self.hardware_message_color)
                surface.blit(msg_surf, (20, self._led_status_y + 18))

        # ── Buttons diagnostics (only on Buttons tab) ──
        if self.active_tab == 3:
            mapping_lbl = self.font.render("Start/Stop", True, COLOR_TEXT)
            surface.blit(mapping_lbl, (20, self.start_stop_label_y))

            pygame.draw.rect(surface, COLOR_STEPPER, self.start_stop_btn_prev, border_radius=6)
            prev_txt = self.font.render("<", True, COLOR_TEXT)
            surface.blit(prev_txt, prev_txt.get_rect(center=self.start_stop_btn_prev.center))

            pygame.draw.rect(surface, COLOR_FIELD_BG, self.start_stop_val_rect, border_radius=6)
            mapped_text = self._start_stop_options[self._start_stop_selected][1]
            map_txt = self.font_small.render(mapped_text, True, COLOR_TEXT)
            surface.blit(map_txt, map_txt.get_rect(center=self.start_stop_val_rect.center))

            pygame.draw.rect(surface, COLOR_STEPPER, self.start_stop_btn_next, border_radius=6)
            next_txt = self.font.render(">", True, COLOR_TEXT)
            surface.blit(next_txt, next_txt.get_rect(center=self.start_stop_btn_next.center))

            button_test_label = "STOP BUTTON TEST" if self.button_test_active else "TEST BUTTONS"
            button_color = COLOR_STOP if self.button_test_active else COLOR_SETTINGS
            self._draw_action_button(surface, self.btn_button_test, button_test_label, button_color)

            button_detected_text = "\u2713 Grove buttons ready" if self.grove_buttons_detected else "\u2717 Grove buttons not detected"
            button_detected_color = COLOR_USB_OK if self.grove_buttons_detected else COLOR_TEXT_DIM
            button_detected = self.font_small.render(button_detected_text, True, button_detected_color)
            surface.blit(button_detected, (14, self._button_status_y))

            self._draw_button_state(surface, "Button 1", "button1", 20, self._button_status_y + 24)
            self._draw_button_state(surface, "Button 2", "button2", 170, self._button_status_y + 24)

            if self.hardware_message:
                message = self.font_small.render(self.hardware_message, True, self.hardware_message_color)
                surface.blit(message, (20, self._button_status_y + 86))

        # ── Save button ──
        pygame.draw.rect(surface, COLOR_SAVE, self.btn_save, border_radius=10)
        save_txt = self.font.render("SAVE", True, COLOR_TEXT)
        surface.blit(save_txt, save_txt.get_rect(center=self.btn_save.center))

        # ── Back button ──
        pygame.draw.rect(surface, COLOR_BACK, self.btn_back, border_radius=10)
        back_txt = self.font.render("BACK", True, COLOR_TEXT)
        surface.blit(back_txt, back_txt.get_rect(center=self.btn_back.center))

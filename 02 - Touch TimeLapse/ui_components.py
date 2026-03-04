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
        self.rect = pygame.Rect(x, y, width, max(height, 80))
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
    """Top bar showing app title, USB status indicator, and photo count."""

    HEIGHT = 40

    def __init__(self, screen_width: int) -> None:
        self.width = screen_width
        self._font_title: Optional[pygame.font.Font] = None
        self._font_info: Optional[pygame.font.Font] = None
        self.usb_connected = False
        self.photo_count = 0

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

    def update(self, usb_connected: bool, photo_count: int) -> None:
        """Update header data (called each frame or on state change)."""
        self.usb_connected = usb_connected
        self.photo_count = photo_count

    def draw(self, surface: pygame.Surface) -> None:
        """Render the header bar."""
        pygame.draw.rect(surface, COLOR_HEADER, (0, 0, self.width, self.HEIGHT))

        # Title
        title = self.font_title.render("PiTimeLapse Touch", True, COLOR_TEXT)
        surface.blit(title, (10, 10))

        # USB indicator
        usb_color = COLOR_USB_OK if self.usb_connected else COLOR_USB_BAD
        usb_char = "\u2713" if self.usb_connected else "\u2717"  # ✓ / ✗
        usb_label = self.font_info.render(f"USB: {usb_char}", True, usb_color)
        surface.blit(usb_label, (self.width - 200, 12))

        # Photo count
        count_surf = self.font_info.render(f"Photos: {self.photo_count}", True, COLOR_TEXT)
        surface.blit(count_surf, (self.width - 110, 12))


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

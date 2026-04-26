"""
grove_status_light.py - WS2813 status light controller for Grove Ring/Stick.

Supports both:
- Grove RGB LED Stick (10 x WS2813 Mini)
- Grove RGB LED Ring (20 x WS2813 Mini)

Implemented as an optional dependency around rpi_ws281x. When the dependency
or GPIO PWM access is unavailable, this controller gracefully disables itself.
"""

from __future__ import annotations

import logging
import os
import platform
import sys
import time
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


def _inject_sudo_user_site_packages() -> None:
    """Expose the invoking user's site-packages when running under sudo.

    On Raspberry Pi setups this project is commonly launched with ``sudo`` so the
    WS281x library can access the required hardware interfaces. If ``rpi_ws281x``
    was installed with ``pip install --user`` for the regular ``pi`` account,
    root's Python environment will not normally see it.

    By prepending the original user's ``~/.local`` site-packages path, both the
    standalone LED tester and the main app can import the dependency without
    forcing a second installation just for root.
    """
    sudo_user = os.environ.get("SUDO_USER")
    if not sudo_user or sudo_user == "root":
        return

    version = f"python{sys.version_info.major}.{sys.version_info.minor}"
    user_site = Path("/home") / sudo_user / ".local" / "lib" / version / "site-packages"
    user_site_str = str(user_site)

    if user_site.exists() and user_site_str not in sys.path:
        sys.path.insert(0, user_site_str)


_inject_sudo_user_site_packages()

try:
    from rpi_ws281x import Color, PixelStrip
    WS281X_AVAILABLE = True
except ImportError:
    WS281X_AVAILABLE = False
    Color = None  # type: ignore[assignment]
    PixelStrip = None  # type: ignore[assignment]


@dataclass(frozen=True)
class RGBColor:
    """Simple RGB color helper for readability."""

    r: int
    g: int
    b: int


STATE_COLORS: dict[str, RGBColor] = {
    "idle": RGBColor(0, 0, 40),         # low blue
    "capturing": RGBColor(0, 60, 0),    # green
    "stopped": RGBColor(40, 20, 0),     # amber
    "error": RGBColor(60, 0, 0),        # red
    "off": RGBColor(0, 0, 0),
}

PALETTE_STATE_COLORS: dict[str, dict[str, RGBColor]] = {
    "classic": {
        "idle": RGBColor(0, 0, 40),
        "capturing": RGBColor(0, 60, 0),
        "stopped": RGBColor(40, 20, 0),
        "error": RGBColor(60, 0, 0),
        "off": RGBColor(0, 0, 0),
    },
    "high_contrast": {
        "idle": RGBColor(0, 0, 90),
        "capturing": RGBColor(0, 110, 0),
        "stopped": RGBColor(110, 65, 0),
        "error": RGBColor(130, 0, 0),
        "off": RGBColor(0, 0, 0),
    },
    "warm": {
        "idle": RGBColor(18, 8, 26),
        "capturing": RGBColor(0, 54, 24),
        "stopped": RGBColor(54, 30, 8),
        "error": RGBColor(72, 8, 8),
        "off": RGBColor(0, 0, 0),
    },
}


class GroveStatusLight:
    """Controls a WS2813 strip/ring to show app state at a glance."""

    def __init__(
        self,
        pin: int = 12,
        pixel_count: int = 10,
        brightness: int = 48,
        state_palette: str = "classic",
        capture_flash_duration_s: float = 0.08,
    ) -> None:
        self.pin = pin
        self.pixel_count = max(1, pixel_count)
        self.brightness = max(0, min(255, brightness))
        self.state_palette = state_palette if state_palette in PALETTE_STATE_COLORS else "classic"
        self.capture_flash_duration_s = max(0.02, min(1.0, capture_flash_duration_s))
        self._state_colors = dict(PALETTE_STATE_COLORS.get(self.state_palette, STATE_COLORS))
        self._strip = None
        self._available = False
        self._last_state = "off"

    def detect(self) -> bool:
        """Initialise the LED strip and return availability."""
        if platform.system() != "Linux":
            logger.info("Grove WS2813 status light only supported on Linux")
            return False

        if not WS281X_AVAILABLE:
            logger.info("rpi_ws281x not found — Grove WS2813 status light disabled")
            return False

        try:
            # Parameters aligned with grove.py defaults.
            self._strip = PixelStrip(
                self.pixel_count,
                self.pin,
                800000,
                10,
                False,
                self.brightness,
                0,
            )
            self._strip.begin()
            self._available = True
            # Default to OFF so LEDs are dark until explicitly needed.
            self.set_state("off")
            logger.info(
                "Grove WS2813 status light ready (pin=%d, pixels=%d)",
                self.pin,
                self.pixel_count,
            )
            return True
        except Exception as exc:
            logger.warning("Could not initialise Grove WS2813 status light: %s", exc)
            self._strip = None
            self._available = False
            return False

    def is_available(self) -> bool:
        return self._available

    def _fill(self, color: RGBColor) -> None:
        if not self._available or self._strip is None:
            return

        c = Color(color.r, color.g, color.b)  # type: ignore[misc]
        for idx in range(self._strip.numPixels()):
            self._strip.setPixelColor(idx, c)
        self._strip.show()

    def set_state(self, state: str) -> None:
        """Set a named steady state color."""
        if state not in self._state_colors:
            state = "off"
        self._fill(self._state_colors[state])
        self._last_state = state

    def flash_capture(self, duration_seconds: float | None = None) -> None:
        """Brief white flash to mark each captured frame."""
        if not self._available:
            return

        duration = self.capture_flash_duration_s if duration_seconds is None else duration_seconds

        self._fill(RGBColor(90, 90, 90))
        time.sleep(max(0.0, duration))
        self.set_state("capturing")

    def set_capture_active(self, active: bool) -> None:
        """Turn the LED bright white (active=True) or back to capturing/off.

        Used by the capture engine to signal the photo moment: ON 1s before
        the snapshot and OFF 1s after, providing a clear visual indicator.
        """
        if not self._available:
            return
        if active:
            self._fill(RGBColor(120, 120, 120))
            self._last_state = "capture_flash"
        else:
            self.set_state("capturing")

    def flash_test(self, duration_seconds: float = 0.25) -> None:
        """Brief bright flash used by the settings diagnostics button."""
        if not self._available:
            return

        previous_state = self._last_state
        self._fill(RGBColor(120, 120, 120))
        time.sleep(max(0.0, duration_seconds))
        self.set_state(previous_state)

    def close(self) -> None:
        """Turn off all pixels and release runtime state."""
        if self._available:
            self.set_state("off")
        self._strip = None
        self._available = False

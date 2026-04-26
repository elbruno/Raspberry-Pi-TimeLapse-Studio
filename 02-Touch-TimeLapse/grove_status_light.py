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
import platform
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

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


class GroveStatusLight:
    """Controls a WS2813 strip/ring to show app state at a glance."""

    def __init__(self, pin: int = 12, pixel_count: int = 10, brightness: int = 48) -> None:
        self.pin = pin
        self.pixel_count = max(1, pixel_count)
        self.brightness = max(0, min(255, brightness))
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
            self.set_state("idle")
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
        if state not in STATE_COLORS:
            state = "off"
        self._fill(STATE_COLORS[state])
        self._last_state = state

    def flash_capture(self, duration_seconds: float = 0.08) -> None:
        """Brief white flash to mark each captured frame."""
        if not self._available:
            return

        self._fill(RGBColor(90, 90, 90))
        time.sleep(max(0.0, duration_seconds))
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

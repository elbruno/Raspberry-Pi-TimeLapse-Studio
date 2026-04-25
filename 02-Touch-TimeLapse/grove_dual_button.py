"""
grove_dual_button.py - Grove Dual Button adapter for Raspberry Pi + Grove Base Hat.

The Grove Dual Button exposes two digital channels over one Grove connector.
On Grove Base Hat for Raspberry Pi, the common mapping is BCM 5 + BCM 6.

This module is intentionally optional:
- On non-RPi systems or when RPi.GPIO is unavailable it degrades to a no-op.
- The app can still run fully in desktop development mode.
"""

from __future__ import annotations

import logging
import platform
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    GPIO = None  # type: ignore[assignment]


@dataclass(frozen=True)
class DualButtonEvent:
    """Single button edge event emitted by the polling adapter."""

    button: str
    timestamp: float


class GroveDualButton:
    """Poll-based dual-button reader with per-button debounce."""

    def __init__(self, pin_button1: int = 5, pin_button2: int = 6, debounce_ms: int = 250) -> None:
        self.pin_button1 = pin_button1
        self.pin_button2 = pin_button2
        self.debounce_ms = max(0, debounce_ms)
        self._available = False
        self._last_state_b1 = 1
        self._last_state_b2 = 1
        self._last_event_b1 = 0.0
        self._last_event_b2 = 0.0

    def detect(self) -> bool:
        """Initialise GPIO and return True when hardware access is ready."""
        if platform.system() != "Linux":
            logger.info("Grove dual button only supported on Linux")
            return False

        if not GPIO_AVAILABLE:
            logger.info("RPi.GPIO not found — Grove dual button disabled")
            return False

        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            # Active LOW buttons with pull-up resistors.
            GPIO.setup(self.pin_button1, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.pin_button2, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            self._last_state_b1 = GPIO.input(self.pin_button1)
            self._last_state_b2 = GPIO.input(self.pin_button2)
            self._available = True
            logger.info(
                "Grove dual button ready on BCM pins %d and %d",
                self.pin_button1,
                self.pin_button2,
            )
            return True
        except Exception as exc:
            logger.warning("Could not initialise Grove dual button: %s", exc)
            self._available = False
            return False

    def is_available(self) -> bool:
        """Return True when GPIO setup succeeded."""
        return self._available

    def poll_events(self) -> list[DualButtonEvent]:
        """Poll current pin states and emit debounced press-edge events."""
        if not self._available:
            return []

        now = time.monotonic()
        events: list[DualButtonEvent] = []

        try:
            state_b1 = GPIO.input(self.pin_button1)  # type: ignore[union-attr]
            state_b2 = GPIO.input(self.pin_button2)  # type: ignore[union-attr]
        except Exception as exc:
            logger.warning("Error reading Grove dual button GPIO: %s", exc)
            return []

        # Active LOW edge detection: HIGH -> LOW means pressed.
        if self._last_state_b1 == 1 and state_b1 == 0:
            if (now - self._last_event_b1) * 1000 >= self.debounce_ms:
                self._last_event_b1 = now
                events.append(DualButtonEvent("button1", time.time()))

        if self._last_state_b2 == 1 and state_b2 == 0:
            if (now - self._last_event_b2) * 1000 >= self.debounce_ms:
                self._last_event_b2 = now
                events.append(DualButtonEvent("button2", time.time()))

        self._last_state_b1 = state_b1
        self._last_state_b2 = state_b2
        return events

    def close(self) -> None:
        """Release button GPIO resources."""
        if not self._available:
            return

        try:
            GPIO.cleanup([self.pin_button1, self.pin_button2])  # type: ignore[union-attr]
        except Exception:
            pass
        finally:
            self._available = False

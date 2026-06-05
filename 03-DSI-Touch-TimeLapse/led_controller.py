"""
led_controller.py - Grove Relay controller used by Scenario 03.

This module controls a Seeed Grove Relay connected to Raspberry Pi GPIO
(through the Grove Base Hat). The relay is switched ON before each capture
and OFF afterward.

Notes:
- Linux only (Raspberry Pi expected)
- Uses sysfs GPIO interface to avoid extra Python dependencies
- Requires permission to write under /sys/class/gpio (typically run with sudo)
"""

import logging
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

GPIO_SYSFS = Path("/sys/class/gpio")


class LEDController:
    """Grove relay controller (keeps legacy class name for compatibility)."""

    def __init__(self, pin: int = 26, active_high: bool = True) -> None:
        self.pin = int(pin)
        self.active_high = bool(active_high)
        self._available: bool = False
        self._exported_here: bool = False
        self._value_path = GPIO_SYSFS / f"gpio{self.pin}" / "value"
        self._direction_path = GPIO_SYSFS / f"gpio{self.pin}" / "direction"

    def detect(self) -> bool:
        """Prepare GPIO pin as output and default relay to OFF."""
        if platform.system() != "Linux":
            logger.info("Relay control only supported on Linux")
            return False

        try:
            GPIO_SYSFS.mkdir(parents=False, exist_ok=True)
        except Exception:
            # Path should already exist on Linux; ignore if mkdir fails.
            pass

        try:
            gpio_dir = GPIO_SYSFS / f"gpio{self.pin}"
            if not gpio_dir.exists():
                (GPIO_SYSFS / "export").write_text(str(self.pin), encoding="utf-8")
                self._exported_here = True

            self._direction_path.write_text("out", encoding="utf-8")
            self._available = True
            self.turn_off()
            logger.info("Relay ready on GPIO pin %d (active_high=%s)", self.pin, self.active_high)
            return True
        except Exception as exc:
            self._available = False
            logger.warning("Unable to initialize relay on GPIO %d: %s", self.pin, exc)
            return False

    def _write_value(self, enabled: bool) -> bool:
        if not self._available:
            return False
        try:
            value = "1" if (enabled == self.active_high) else "0"
            self._value_path.write_text(value, encoding="utf-8")
            return True
        except Exception as exc:
            logger.warning("Failed to set relay state on GPIO %d: %s", self.pin, exc)
            return False

    def is_available(self) -> bool:
        return self._available

    def turn_on(self) -> bool:
        """Close relay contact (or open for active-low)."""
        return self._write_value(True)

    def turn_off(self) -> bool:
        """Open relay contact (or close for active-low)."""
        return self._write_value(False)

    def close(self) -> None:
        """Set relay to OFF and optionally unexport pin."""
        if self._available:
            self.turn_off()
            logger.info("Relay controller closed (GPIO %d)", self.pin)
        try:
            if self._exported_here:
                (GPIO_SYSFS / "unexport").write_text(str(self.pin), encoding="utf-8")
        except Exception:
            # Leaving exported pin is acceptable.
            pass
        self._available = False

    @property
    def port_name(self) -> str:
        return f"GPIO{self.pin}"

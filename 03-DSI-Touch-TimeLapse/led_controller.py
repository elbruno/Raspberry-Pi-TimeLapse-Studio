"""
led_controller.py - Grove Relay controller used by Scenario 03.

This module controls a Seeed Grove Relay connected to Raspberry Pi GPIO
(through the Grove Base Hat). The relay is switched ON before each capture
and OFF afterward.

Notes:
- Linux only (Raspberry Pi expected)
- Prefers RPi.GPIO backend (same as grove_dual_button) on modern Pi OS
- Falls back to sysfs GPIO for compatibility on environments without RPi.GPIO
"""

import logging
import platform
from pathlib import Path

logger = logging.getLogger(__name__)

GPIO_SYSFS = Path("/sys/class/gpio")

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    GPIO = None  # type: ignore[assignment]


class LEDController:
    """Grove relay controller (keeps legacy class name for compatibility)."""

    def __init__(self, pin: int = 26, active_high: bool = True) -> None:
        self.pin = int(pin)
        self.active_high = bool(active_high)
        self._available: bool = False
        self._backend: str = "none"
        self._exported_here: bool = False
        self._value_path = GPIO_SYSFS / f"gpio{self.pin}" / "value"
        self._direction_path = GPIO_SYSFS / f"gpio{self.pin}" / "direction"

    def _detect_rpi_gpio(self) -> bool:
        """Initialize relay pin using RPi.GPIO (preferred on Raspberry Pi)."""
        if not GPIO_AVAILABLE:
            return False

        try:
            GPIO.setwarnings(False)  # type: ignore[union-attr]
            GPIO.setmode(GPIO.BCM)  # type: ignore[union-attr]

            # Keep relay OFF on setup to avoid accidental pulse.
            off_level_high = (False == self.active_high)
            initial_level = GPIO.HIGH if off_level_high else GPIO.LOW  # type: ignore[union-attr]
            GPIO.setup(self.pin, GPIO.OUT, initial=initial_level)  # type: ignore[union-attr]

            self._available = True
            self._backend = "rpi_gpio"
            logger.info(
                "Relay ready on GPIO pin %d (active_high=%s, backend=RPi.GPIO)",
                self.pin,
                self.active_high,
            )
            return True
        except Exception as exc:
            logger.warning("RPi.GPIO init failed for GPIO %d: %s", self.pin, exc)
            return False

    def _detect_sysfs(self) -> bool:
        """Initialize relay pin using legacy sysfs GPIO interface."""
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
            self._backend = "sysfs"
            self.turn_off()
            logger.info(
                "Relay ready on GPIO pin %d (active_high=%s, backend=sysfs)",
                self.pin,
                self.active_high,
            )
            return True
        except Exception as exc:
            self._available = False
            logger.warning("Unable to initialize relay on GPIO %d: %s", self.pin, exc)
            return False

    def detect(self) -> bool:
        """Prepare GPIO pin as output and default relay to OFF."""
        if platform.system() != "Linux":
            logger.info("Relay control only supported on Linux")
            return False

        # Prefer RPi.GPIO on Raspberry Pi OS Bookworm and newer. Sysfs GPIO is
        # deprecated and may return EINVAL when writing /sys/class/gpio/export.
        if self._detect_rpi_gpio():
            return True

        return self._detect_sysfs()

    def _write_value(self, enabled: bool) -> bool:
        if not self._available:
            return False
        try:
            level_high = (enabled == self.active_high)

            if self._backend == "rpi_gpio" and GPIO_AVAILABLE:
                level = GPIO.HIGH if level_high else GPIO.LOW  # type: ignore[union-attr]
                GPIO.output(self.pin, level)  # type: ignore[union-attr]
                return True

            value = "1" if level_high else "0"
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

        if self._backend == "rpi_gpio" and GPIO_AVAILABLE:
            try:
                GPIO.cleanup([self.pin])  # type: ignore[union-attr]
            except Exception:
                pass

        try:
            if self._backend == "sysfs" and self._exported_here:
                (GPIO_SYSFS / "unexport").write_text(str(self.pin), encoding="utf-8")
        except Exception:
            # Leaving exported pin is acceptable.
            pass
        self._available = False
        self._backend = "none"

    @property
    def port_name(self) -> str:
        return f"GPIO{self.pin}"

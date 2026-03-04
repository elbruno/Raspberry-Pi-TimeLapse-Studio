"""
led_controller.py - USB LED Light Controller for Touch TimeLapse

Auto-detects USB relay modules (e.g. LCUS-1, SainSmart, HiLetgo) and
provides simple on/off control.  The LED is turned on before each photo
capture to illuminate the scene, then turned off afterward.

If no USB relay is detected, all operations are silent no-ops — the
rest of the app works exactly the same.

Supported hardware:
    - LCUS-1 type USB relay modules (CH340/CH341 chip)
    - Most single-channel USB relay boards using the 0xA0 protocol
    - Devices that appear as /dev/ttyUSB* or COM* serial ports

Usage:
    led = LEDController()
    if led.is_available():
        led.turn_on()
        time.sleep(1)
        led.turn_off()
    led.close()
"""

import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

# Optional dependency — pyserial may not be installed
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False
    serial = None  # type: ignore[assignment]
    logger.info(
        "pyserial is not installed — USB LED control disabled. "
        "Install with: pip install pyserial"
    )

# Common USB relay protocol (LCUS-1 / generic single-channel relay)
# Format: 0xA0  channel  state  checksum
_CMD_RELAY_ON = bytes([0xA0, 0x01, 0x01, 0xA2])
_CMD_RELAY_OFF = bytes([0xA0, 0x01, 0x00, 0xA1])
_BAUD_RATE = 9600

# USB vendor/product hints for common relay modules
_RELAY_KEYWORDS = [
    "ch340", "ch341",       # Most common relay chip
    "usb serial",           # Generic USB-serial adapters
    "usb-serial",
    "relay",
    "ft232",                # FTDI-based relays
    "cp210",                # CP2102-based relays
    "pl2303",               # Prolific-based
]


class LEDController:
    """USB relay-based LED controller with auto-detection.

    On init, scans USB serial ports for likely relay modules.
    If none found, all methods are safe no-ops.
    """

    def __init__(self) -> None:
        self._port: Optional[serial.Serial] = None  # type: ignore[name-defined]
        self._port_name: Optional[str] = None
        self._available: bool = False

    def detect(self) -> bool:
        """Scan for a USB relay device and open the first one found.

        Returns True if a relay was found and opened.
        """
        if not SERIAL_AVAILABLE:
            return False

        try:
            ports = serial.tools.list_ports.comports()
            for port_info in ports:
                desc = (port_info.description or "").lower()
                hwid = (port_info.hwid or "").lower()
                combined = f"{desc} {hwid}"

                # Match against known relay/serial adapter keywords
                if any(kw in combined for kw in _RELAY_KEYWORDS):
                    if self._try_open(port_info.device):
                        return True

            # Fallback: try any /dev/ttyUSB* port (Linux Pi typical)
            for port_info in ports:
                device = port_info.device or ""
                if "ttyUSB" in device or "ttyACM" in device:
                    if self._try_open(device):
                        return True

        except Exception as exc:
            logger.warning("LED detection error: %s", exc)

        logger.info("No USB LED/relay device detected — LED control disabled")
        return False

    def _try_open(self, device: str) -> bool:
        """Attempt to open a serial port as a relay device."""
        try:
            self._port = serial.Serial(
                port=device,
                baudrate=_BAUD_RATE,
                timeout=1,
                write_timeout=1,
            )
            self._port_name = device
            self._available = True
            # Start with relay OFF
            self._port.write(_CMD_RELAY_OFF)
            time.sleep(0.1)
            logger.info("USB LED relay detected on %s", device)
            return True
        except Exception as exc:
            logger.debug("Could not open %s as relay: %s", device, exc)
            if self._port is not None:
                try:
                    self._port.close()
                except Exception:
                    pass
            self._port = None
            self._available = False
            return False

    def is_available(self) -> bool:
        """Return True if a USB relay was detected and is open."""
        return self._available and self._port is not None

    def turn_on(self) -> bool:
        """Turn the LED relay ON. Returns True on success."""
        if not self.is_available():
            return False
        try:
            self._port.write(_CMD_RELAY_ON)  # type: ignore[union-attr]
            logger.debug("LED ON (%s)", self._port_name)
            return True
        except Exception as exc:
            logger.warning("Failed to turn LED on: %s", exc)
            return False

    def turn_off(self) -> bool:
        """Turn the LED relay OFF. Returns True on success."""
        if not self.is_available():
            return False
        try:
            self._port.write(_CMD_RELAY_OFF)  # type: ignore[union-attr]
            logger.debug("LED OFF (%s)", self._port_name)
            return True
        except Exception as exc:
            logger.warning("Failed to turn LED off: %s", exc)
            return False

    def close(self) -> None:
        """Turn off the relay and close the serial port."""
        if self._port is not None:
            try:
                self._port.write(_CMD_RELAY_OFF)
                time.sleep(0.05)
                self._port.close()
                logger.info("LED controller closed (%s)", self._port_name)
            except Exception as exc:
                logger.warning("Error closing LED controller: %s", exc)
        self._port = None
        self._available = False
        self._port_name = None

    @property
    def port_name(self) -> Optional[str]:
        """The serial port device name, or None."""
        return self._port_name

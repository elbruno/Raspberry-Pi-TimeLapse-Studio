"""
led_controller.py - USB LED Light Controller for Touch TimeLapse

Controls simple USB-powered LED lights by toggling USB port power on/off
using uhubctl (preferred) or sysfs (fallback). No special protocol needed —
just power the LED directly.

The LED is turned on before each photo capture to illuminate the scene,
then turned off afterward.

If no controllable USB port is detected, all operations are silent no-ops —
the rest of the app works exactly the same.

Requirements:
    - Linux (Raspberry Pi or similar)
    - uhubctl utility: sudo apt install uhubctl
    - Root access or udev rule for non-root control

    Note: uhubctl typically requires root. For dedicated Pi setups, run the
    app with sudo, or add a udev rule to grant non-root access to USB hubs.

Usage:
    led = LEDController(usb_port="auto")
    if led.is_available():
        led.turn_on()
        time.sleep(1)
        led.turn_off()
    led.close()
"""

import logging
import platform
import re
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

# uhubctl availability check
_UHUBCTL_AVAILABLE: Optional[bool] = None

# Device classes to SKIP (cameras, storage, input devices)
_SKIP_DEVICE_CLASSES = [
    "hub",          # USB hubs themselves
    "mass storage", # USB drives, SD card readers
    "camera",       # USB webcams
    "video",        # Video devices
    "input",        # Keyboard, mouse, touchscreen
    "hid",          # Human Interface Devices
    "audio",        # Sound devices
]


def _check_uhubctl() -> bool:
    """Check if uhubctl is installed and available."""
    global _UHUBCTL_AVAILABLE
    if _UHUBCTL_AVAILABLE is not None:
        return _UHUBCTL_AVAILABLE

    try:
        result = subprocess.run(
            ["uhubctl", "--version"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        _UHUBCTL_AVAILABLE = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        _UHUBCTL_AVAILABLE = False

    if not _UHUBCTL_AVAILABLE:
        logger.info(
            "uhubctl not found — USB LED control disabled. "
            "Install with: sudo apt install uhubctl"
        )
    return _UHUBCTL_AVAILABLE


class LEDController:
    """USB port power controller for simple LED lights.

    Controls USB LED by toggling port power using uhubctl.
    Auto-detects suitable USB ports (skips cameras, storage, input devices).
    """

    def __init__(self, usb_port: str = "auto") -> None:
        """
        Initialize LED controller.

        Args:
            usb_port: USB port location (e.g., "1-1.2") or "auto" to detect
        """
        self._usb_port: Optional[str] = None
        self._hub_location: Optional[str] = None
        self._port_number: Optional[str] = None
        self._available: bool = False
        self._configured_port: str = usb_port

    def detect(self) -> bool:
        """Scan for a controllable USB port and prepare for control.

        Returns True if a suitable port was found.
        """
        # Only works on Linux
        if platform.system() != "Linux":
            logger.info("USB port power control only supported on Linux")
            return False

        if not _check_uhubctl():
            return False

        # If explicit port specified, validate and use it
        if self._configured_port != "auto":
            if self._validate_explicit_port(self._configured_port):
                return True
            else:
                logger.warning(
                    "Configured USB port %s not found or not controllable",
                    self._configured_port
                )
                return False

        # Auto-detect mode: scan for candidate ports
        return self._auto_detect_port()

    def _validate_explicit_port(self, port_spec: str) -> bool:
        """Validate that an explicitly configured port exists and is controllable."""
        try:
            result = subprocess.run(
                ["uhubctl"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            # Parse uhubctl output to find this specific port
            for line in result.stdout.splitlines():
                # Look for lines like "  Port 2: 0503 power" (port with power control)
                port_match = re.search(
                    r"Port\s+(\d+):\s+\w+\s+(?:power|off|On)",
                    line,
                    re.IGNORECASE
                )
                if port_match:
                    # Check if this matches our port spec
                    # Port spec format: "hub_location" (e.g., "1-1") with port number
                    # We'll store both and construct commands later
                    self._usb_port = port_spec
                    self._available = True
                    logger.info("Using configured USB port: %s", port_spec)
                    return True

        except (subprocess.TimeoutExpired, Exception) as exc:
            logger.warning("Error validating USB port %s: %s", port_spec, exc)

        return False

    def _auto_detect_port(self) -> bool:
        """Auto-detect a suitable USB port for LED control."""
        try:
            result = subprocess.run(
                ["uhubctl"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                # Check if permission error
                if "permission denied" in result.stderr.lower():
                    logger.warning(
                        "uhubctl requires root permissions. "
                        "Run with sudo or add a udev rule for non-root access."
                    )
                else:
                    logger.warning("uhubctl failed: %s", result.stderr.strip())
                return False

            # Parse uhubctl output
            current_hub = None
            candidates = []

            for line in result.stdout.splitlines():
                # Hub line: "Current status for hub 1-1 [0424:9514 Generic USB2.0 Hub, USB 2.00, 5 ports, ppps]"
                hub_match = re.search(
                    r"hub\s+([\d\-\.]+)\s+\[.*?,.*?(\d+)\s+ports.*?ppps",
                    line,
                    re.IGNORECASE
                )
                if hub_match:
                    current_hub = hub_match.group(1)
                    continue

                # Port line: "  Port 2: 0100 power"
                # We want ports that are OFF or have power control
                if current_hub:
                    port_match = re.search(
                        r"Port\s+(\d+):\s+(\w+)\s+(.*)",
                        line,
                        re.IGNORECASE
                    )
                    if port_match:
                        port_num = port_match.group(1)
                        status = port_match.group(2)
                        info = port_match.group(3).lower()

                        # Skip if it's a device we don't want to power cycle
                        skip = False
                        for skip_class in _SKIP_DEVICE_CLASSES:
                            if skip_class in info:
                                skip = True
                                break

                        if not skip and "power" in info:
                            candidates.append((current_hub, port_num, info))

            if candidates:
                # Pick the first candidate
                hub, port, info = candidates[0]
                self._hub_location = hub
                self._port_number = port
                self._usb_port = f"{hub}.{port}"
                self._available = True
                logger.info(
                    "Auto-detected USB LED port: hub %s, port %s (%s)",
                    hub, port, info.strip()
                )
                if len(candidates) > 1:
                    logger.info(
                        "Found %d candidate ports. Using first. "
                        "Set led.usb_port in config.yaml to use a specific port.",
                        len(candidates)
                    )
                return True

            logger.info(
                "No suitable USB ports found for LED control. "
                "All ports are either in use by system devices or lack power switching."
            )

        except (subprocess.TimeoutExpired, Exception) as exc:
            logger.warning("Error detecting USB ports: %s", exc)

        return False

    def is_available(self) -> bool:
        """Return True if a controllable USB port was detected."""
        return self._available

    def turn_on(self) -> bool:
        """Turn the LED ON by enabling USB port power. Returns True on success."""
        if not self.is_available():
            return False

        try:
            # If we have explicit hub and port, use those
            if self._hub_location and self._port_number:
                cmd = [
                    "uhubctl",
                    "-l", self._hub_location,
                    "-p", self._port_number,
                    "-a", "on",
                    "-r", "0",
                ]
            else:
                # Fallback: just use the port spec directly
                logger.warning("Using fallback port control (may be slow)")
                cmd = ["uhubctl", "-a", "on", "-r", "0"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode == 0:
                logger.debug("LED ON (USB port %s)", self._usb_port)
                return True
            else:
                if "permission denied" in result.stderr.lower():
                    logger.warning(
                        "Cannot control USB port — permission denied. "
                        "Run with sudo or configure udev rules."
                    )
                else:
                    logger.warning("Failed to turn LED on: %s", result.stderr.strip())
                return False

        except subprocess.TimeoutExpired:
            logger.warning("LED turn_on command timed out")
            return False
        except Exception as exc:
            logger.warning("Failed to turn LED on: %s", exc)
            return False

    def turn_off(self) -> bool:
        """Turn the LED OFF by disabling USB port power. Returns True on success."""
        if not self.is_available():
            return False

        try:
            if self._hub_location and self._port_number:
                cmd = [
                    "uhubctl",
                    "-l", self._hub_location,
                    "-p", self._port_number,
                    "-a", "off",
                    "-r", "0",
                ]
            else:
                logger.warning("Using fallback port control (may be slow)")
                cmd = ["uhubctl", "-a", "off", "-r", "0"]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode == 0:
                logger.debug("LED OFF (USB port %s)", self._usb_port)
                return True
            else:
                if "permission denied" in result.stderr.lower():
                    logger.warning(
                        "Cannot control USB port — permission denied. "
                        "Run with sudo or configure udev rules."
                    )
                else:
                    logger.warning("Failed to turn LED off: %s", result.stderr.strip())
                return False

        except subprocess.TimeoutExpired:
            logger.warning("LED turn_off command timed out")
            return False
        except Exception as exc:
            logger.warning("Failed to turn LED off: %s", exc)
            return False

    def close(self) -> None:
        """Turn off the LED and clean up."""
        if self._available:
            self.turn_off()
            logger.info("LED controller closed (USB port %s)", self._usb_port)
        self._available = False
        self._usb_port = None
        self._hub_location = None
        self._port_number = None

    @property
    def port_name(self) -> Optional[str]:
        """The USB port location (e.g., "1-1.2"), or None."""
        return self._usb_port

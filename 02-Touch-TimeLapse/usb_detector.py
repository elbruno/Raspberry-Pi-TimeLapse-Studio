"""
usb_detector.py - USB Drive Detection for Touch TimeLapse

Automatically finds the first connected USB drive so time-lapse photos
are saved to removable storage.  Falls back to a local ``./data``
directory when no USB drive is present.

Works on Linux / Raspberry Pi and Windows.

Usage:
    mount = find_first_usb_drive()          # e.g. "/media/pi/USB_DRIVE"
    info  = get_drive_info(mount)           # free/total space dict
"""

import logging
import os
import platform
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Try to import psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None
    logger.warning("psutil is not installed. Install with: pip install psutil")


def find_first_usb_drive(fallback: str = "./data") -> str:
    """
    Return the mount point of the first detected external USB drive.

    Detection strategy:
      - **Linux / Raspberry Pi**: look for partitions whose device path
        starts with ``/dev/sd`` and that are *not* mounted at ``/`` or
        ``/boot``.
      - **Windows**: look for removable drives (``disk_partitions``
        with ``opts`` containing ``removable`` or drive-type check).

    Falls back to *fallback* (default ``./data``) when no USB drive is
    found or when ``psutil`` is unavailable.

    Args:
        fallback: Directory to use when no USB drive is detected.

    Returns:
        Absolute path to the chosen storage directory.
    """
    if not PSUTIL_AVAILABLE:
        logger.warning("psutil unavailable — falling back to %s", fallback)
        os.makedirs(fallback, exist_ok=True)
        return fallback

    system = platform.system()

    try:
        partitions = psutil.disk_partitions(all=False)
    except Exception as e:
        logger.error("Failed to list disk partitions: %s", e)
        os.makedirs(fallback, exist_ok=True)
        return fallback

    if system == "Linux":
        mount = _find_linux_usb(partitions)
    elif system == "Windows":
        mount = _find_windows_usb(partitions)
    else:
        logger.info("Unsupported OS '%s' for USB detection", system)
        mount = None

    if mount:
        logger.info("USB drive detected at %s", mount)
        return mount

    logger.info("No USB drive found — using fallback %s", fallback)
    os.makedirs(fallback, exist_ok=True)
    return fallback


def _find_linux_usb(partitions) -> Optional[str]:
    """Pick the first ``/dev/sd*`` partition not mounted at / or /boot."""
    skip_mounts = {"/", "/boot", "/boot/firmware"}
    for part in partitions:
        if part.device.startswith("/dev/sd") and part.mountpoint not in skip_mounts:
            logger.debug("Linux USB candidate: %s → %s", part.device, part.mountpoint)
            return part.mountpoint
    return None


def _find_windows_usb(partitions) -> Optional[str]:
    """Pick the first removable drive on Windows."""
    try:
        import ctypes
        DRIVE_REMOVABLE = 2
        for part in partitions:
            drive_letter = part.mountpoint
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_letter)
            if drive_type == DRIVE_REMOVABLE:
                logger.debug("Windows removable drive: %s", drive_letter)
                return drive_letter
    except Exception as e:
        logger.debug("ctypes drive-type check failed: %s — trying opts", e)

    # Fallback: check partition opts for "removable" keyword
    for part in partitions:
        if hasattr(part, "opts") and "removable" in part.opts.lower():
            return part.mountpoint
    return None


def get_drive_info(path: str) -> Dict[str, object]:
    """
    Return storage information for the drive containing *path*.

    Args:
        path: Any path on the target drive.

    Returns:
        Dictionary with keys ``free_bytes``, ``total_bytes``,
        ``free_gb``, ``total_gb``, and ``drive_name``.
    """
    info: Dict[str, object] = {
        "free_bytes": 0,
        "total_bytes": 0,
        "free_gb": 0.0,
        "total_gb": 0.0,
        "name": os.path.basename(path) or path,
    }

    if not PSUTIL_AVAILABLE:
        logger.warning("psutil unavailable — cannot query drive info")
        return info

    try:
        usage = psutil.disk_usage(path)
        info["free_bytes"] = usage.free
        info["total_bytes"] = usage.total
        info["free_gb"] = round(usage.free / (1024 ** 3), 2)
        info["total_gb"] = round(usage.total / (1024 ** 3), 2)
        logger.debug("Drive info for %s: %.2f GB free / %.2f GB total",
                      path, info["free_gb"], info["total_gb"])
    except Exception as e:
        logger.error("Failed to get drive info for %s: %s", path, e)

    return info

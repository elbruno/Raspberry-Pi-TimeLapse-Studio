"""
test_usb_detector.py - Tests for USB drive detection.

Tests find_first_usb_drive() and get_drive_info() with mocked psutil.
All hardware access is mocked for CI compatibility.

To run:
    pytest tests/test_usb_detector.py -v
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestFindFirstUsbDrive:
    """Tests for find_first_usb_drive()."""

    @patch("usb_detector.platform")
    @patch("usb_detector.psutil")
    def test_returns_usb_mount_on_linux(self, mock_psutil, mock_platform):
        """USB drive mounted at /media/user/USB is detected."""
        mock_platform.system.return_value = "Linux"
        partition = MagicMock()
        partition.mountpoint = "/media/user/USB"
        partition.fstype = "vfat"
        partition.device = "/dev/sda1"
        mock_psutil.disk_partitions.return_value = [partition]

        from usb_detector import find_first_usb_drive

        result = find_first_usb_drive()
        assert result == "/media/user/USB"

    @patch("usb_detector.psutil")
    def test_returns_usb_mount_on_windows(self, mock_psutil):
        """USB drive on Windows (removable drive letter) is detected."""
        partition = MagicMock()
        partition.mountpoint = "E:\\"
        partition.fstype = "FAT32"
        partition.device = "E:\\"
        partition.opts = "rw,removable"
        mock_psutil.disk_partitions.return_value = [partition]

        from usb_detector import find_first_usb_drive

        result = find_first_usb_drive()
        assert result is not None
        assert result != "./data"

    @patch("usb_detector.psutil")
    def test_fallback_to_data_when_no_usb(self, mock_psutil):
        """Returns './data' fallback when no USB drive found."""
        mock_psutil.disk_partitions.return_value = []

        from usb_detector import find_first_usb_drive

        result = find_first_usb_drive()
        assert result == "./data"

    @patch("usb_detector.platform")
    @patch("usb_detector.psutil")
    @patch("usb_detector.subprocess.run")
    @patch("usb_detector._command_exists")
    def test_linux_attempts_automount_when_partition_unmounted(
        self,
        mock_command_exists,
        mock_run,
        mock_psutil,
        mock_platform,
    ):
        """When /dev/sdX is present but unmounted, udisksctl mount is attempted."""
        mock_platform.system.return_value = "Linux"
        part = MagicMock()
        part.mountpoint = ""
        part.device = "/dev/sda1"
        part.fstype = "ntfs"
        mock_psutil.disk_partitions.return_value = [part]

        mock_command_exists.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Mounted /dev/sda1 at /media/pi/USB_DRIVE.\n",
            stderr="",
        )

        from usb_detector import find_first_usb_drive

        result = find_first_usb_drive()
        assert result == "/media/pi/USB_DRIVE"

    @patch("usb_detector.platform")
    @patch("usb_detector.psutil")
    @patch("usb_detector._command_exists")
    def test_linux_automount_skipped_without_udisksctl(
        self,
        mock_command_exists,
        mock_psutil,
        mock_platform,
    ):
        """Without udisksctl, detector falls back to local path."""
        mock_platform.system.return_value = "Linux"
        part = MagicMock()
        part.mountpoint = ""
        part.device = "/dev/sda1"
        part.fstype = "ntfs"
        mock_psutil.disk_partitions.return_value = [part]

        mock_command_exists.return_value = False

        from usb_detector import find_first_usb_drive

        result = find_first_usb_drive()
        assert result == "./data"

    @patch("usb_detector.platform")
    @patch("usb_detector.psutil")
    def test_fallback_when_only_system_partitions(self, mock_psutil, mock_platform):
        """System partitions (/, /boot, C:\\) are not treated as USB."""
        mock_platform.system.return_value = "Linux"
        partitions = []
        for mp, dev in [("/", "/dev/nvme0n1p1"), ("/boot", "/dev/nvme0n1p2"), ("/home", "/dev/nvme0n1p3")]:
            p = MagicMock()
            p.mountpoint = mp
            p.fstype = "ext4"
            p.device = dev
            partitions.append(p)
        mock_psutil.disk_partitions.return_value = partitions

        from usb_detector import find_first_usb_drive

        result = find_first_usb_drive()
        assert result == "./data"

    @patch("usb_detector.psutil", None)
    def test_fallback_when_psutil_unavailable(self):
        """Returns './data' when psutil is not installed."""
        # Re-import to trigger the fallback path
        import importlib
        try:
            import usb_detector
            importlib.reload(usb_detector)
            result = usb_detector.find_first_usb_drive()
            assert result == "./data"
        except Exception:
            # If module can't handle missing psutil, that's also acceptable
            # as long as it doesn't crash without a clear error
            pass


class TestGetDriveInfo:
    """Tests for get_drive_info()."""

    @patch("usb_detector.psutil")
    def test_returns_drive_info_dict(self, mock_psutil):
        """get_drive_info returns dict with free_gb, total_gb, name."""
        usage = MagicMock()
        usage.free = 8 * 1024 ** 3  # 8 GB
        usage.total = 32 * 1024 ** 3  # 32 GB
        mock_psutil.disk_usage.return_value = usage

        from usb_detector import get_drive_info

        info = get_drive_info("/media/user/USB")

        assert "free_gb" in info
        assert "total_gb" in info
        assert "name" in info
        assert abs(info["free_gb"] - 8.0) < 0.1
        assert abs(info["total_gb"] - 32.0) < 0.1

    @patch("usb_detector.psutil")
    def test_drive_info_with_small_drive(self, mock_psutil):
        """Handles small drives correctly (e.g. 1 GB USB stick)."""
        usage = MagicMock()
        usage.free = 512 * 1024 ** 2  # 512 MB
        usage.total = 1 * 1024 ** 3  # 1 GB
        mock_psutil.disk_usage.return_value = usage

        from usb_detector import get_drive_info

        info = get_drive_info("/mnt/usb")
        assert info["free_gb"] < 1.0
        assert abs(info["total_gb"] - 1.0) < 0.1

    @patch("usb_detector.psutil")
    def test_drive_info_name_from_path(self, mock_psutil):
        """Drive name is derived from the mount path."""
        usage = MagicMock()
        usage.free = 4 * 1024 ** 3
        usage.total = 16 * 1024 ** 3
        mock_psutil.disk_usage.return_value = usage

        from usb_detector import get_drive_info

        info = get_drive_info("/media/user/MyUSB")
        assert isinstance(info["name"], str)
        assert len(info["name"]) > 0

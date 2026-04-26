"""
test_camera.py - Tests for OpenCV camera abstraction.

Tests OpenCVCamera with fully mocked cv2 for CI compatibility.
No real camera hardware is needed.

To run:
    pytest tests/test_camera.py -v
"""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock


class TestOpenCVCamera:
    """Tests for the OpenCVCamera class."""

    @patch("camera_opencv.cv2", new_callable=MagicMock)
    def test_is_available_when_cv2_present(self, mock_cv2):
        """is_available() returns True when cv2 is importable."""
        from camera_opencv import OpenCVCamera

        camera = OpenCVCamera()
        assert camera.is_available() is True

    @patch("camera_opencv.OPENCV_AVAILABLE", False)
    def test_is_available_when_cv2_missing(self):
        """is_available() returns False when cv2 is not installed."""
        from camera_opencv import OpenCVCamera

        camera = OpenCVCamera()
        assert camera.is_available() is False

    @patch("camera_opencv.cv2")
    def test_open_success(self, mock_cv2):
        """open() returns True when camera opens successfully."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cv2.VideoCapture.return_value = mock_cap

        from camera_opencv import OpenCVCamera

        camera = OpenCVCamera()
        result = camera.open(camera_index=0, width=1280, height=720)

        assert result is True
        assert mock_cv2.VideoCapture.call_count >= 1
        first_args = mock_cv2.VideoCapture.call_args_list[0].args
        assert first_args[0] == 0
        mock_cap.set.assert_any_call(mock_cv2.CAP_PROP_FRAME_WIDTH, 1280)
        mock_cap.set.assert_any_call(mock_cv2.CAP_PROP_FRAME_HEIGHT, 720)

    @patch("camera_opencv.cv2")
    def test_open_failure(self, mock_cv2):
        """open() returns False when camera fails to open."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = False
        mock_cv2.VideoCapture.return_value = mock_cap

        from camera_opencv import OpenCVCamera

        camera = OpenCVCamera()
        result = camera.open(camera_index=0, width=640, height=480)

        assert result is False

    @patch("camera_opencv.cv2")
    def test_capture_returns_numpy_array(self, mock_cv2):
        """capture() returns a numpy array on success."""
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.grab.return_value = False
        mock_cap.read.return_value = (True, fake_frame)
        mock_cv2.VideoCapture.return_value = mock_cap

        from camera_opencv import OpenCVCamera

        camera = OpenCVCamera()
        camera.open(camera_index=0, width=640, height=480)
        frame = camera.capture()

        assert isinstance(frame, np.ndarray)
        assert frame.shape == (480, 640, 3)

    @patch("camera_opencv.cv2")
    def test_capture_returns_none_on_failure(self, mock_cv2):
        """capture() returns None when read fails."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.grab.return_value = False
        mock_cap.read.return_value = (False, None)
        mock_cv2.VideoCapture.return_value = mock_cap

        from camera_opencv import OpenCVCamera

        camera = OpenCVCamera()
        camera.open(camera_index=0, width=640, height=480)
        frame = camera.capture()

        assert frame is None

    @patch("camera_opencv.cv2")
    def test_close_releases_camera(self, mock_cv2):
        """close() releases the VideoCapture resource."""
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cv2.VideoCapture.return_value = mock_cap

        from camera_opencv import OpenCVCamera

        camera = OpenCVCamera()
        camera.open(camera_index=0, width=640, height=480)
        camera.close()

        mock_cap.release.assert_called_once()

    @patch("camera_opencv.cv2")
    def test_close_without_open_does_not_crash(self, mock_cv2):
        """close() is safe to call even if camera was never opened."""
        from camera_opencv import OpenCVCamera

        camera = OpenCVCamera()
        # Should not raise
        camera.close()

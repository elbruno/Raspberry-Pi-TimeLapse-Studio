"""
camera_opencv.py - OpenCV Camera for Touch TimeLapse

Simplified camera driver using OpenCV.  Handles USB webcams on any
platform and suppresses the noisy stderr output that OpenCV sometimes
produces.

Usage:
    camera = OpenCVCamera()
    if camera.open(0, 640, 480):
        frame = camera.capture()   # numpy.ndarray or None
        camera.close()
"""

import logging
import os
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Optional dependency — OpenCV may not be installed
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    logger.warning(
        "OpenCV (cv2) is not installed. "
        "Install with: pip install opencv-python-headless"
    )


class OpenCVCamera:
    """USB / built-in camera driver backed by OpenCV."""

    def __init__(self) -> None:
        self.cap = None
        self.resolution: Tuple[int, int] = (640, 480)
        self._is_open: bool = False

    def is_available(self) -> bool:
        """Return True when the OpenCV library is importable."""
        return OPENCV_AVAILABLE

    def open(self, camera_index: int = 0, width: int = 640, height: int = 480) -> bool:
        """
        Open a camera device and set the requested resolution.

        Args:
            camera_index: /dev/videoN index (0 = first camera).
            width:  Desired frame width.
            height: Desired frame height.

        Returns:
            True on success, False otherwise.
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV is not available — cannot open camera")
            return False

        try:
            # Suppress OpenCV stderr noise while probing the device
            devnull = os.open(os.devnull, os.O_WRONLY)
            old_stderr_fd = os.dup(2)
            os.dup2(devnull, 2)
            os.close(devnull)

            try:
                self.cap = cv2.VideoCapture(camera_index)

                if not self.cap.isOpened():
                    logger.warning(
                        "No camera found at index %d. "
                        "Check connection or try a different index.", camera_index
                    )
                    return False

                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

                actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.resolution = (actual_w, actual_h)

                # Warm-up frames so auto-exposure stabilises
                for _ in range(3):
                    self.cap.read()

                self._is_open = True
                logger.info("Camera opened — resolution %dx%d", actual_w, actual_h)
                return True

            finally:
                os.dup2(old_stderr_fd, 2)
                os.close(old_stderr_fd)

        except Exception as e:
            logger.error("Error opening camera: %s", e)
            return False

    def capture(self) -> Optional[np.ndarray]:
        """
        Grab a single frame from the camera.

        Returns:
            BGR numpy array, or None on failure.
        """
        if not self._is_open or self.cap is None:
            logger.error("Camera is not open — call open() first")
            return None

        try:
            ret, frame = self.cap.read()
            if ret and frame is not None:
                return frame
            logger.error("Failed to capture frame")
            return None
        except Exception as e:
            logger.error("Capture error: %s", e)
            return None

    def close(self) -> None:
        """Release the camera device."""
        if self.cap is not None:
            try:
                self.cap.release()
                logger.info("Camera closed")
            except Exception as e:
                logger.warning("Error closing camera: %s", e)
        self.cap = None
        self._is_open = False

    def is_open(self) -> bool:
        """Check whether the camera is currently open."""
        return self._is_open and self.cap is not None and self.cap.isOpened()

"""
camera_opencv.py - OpenCV Camera Implementation

This file implements camera capture using OpenCV (cv2).
OpenCV works with most USB webcams and is cross-platform.

OpenCV is a popular computer vision library. We use it here as a
fallback camera option that works on any computer with a webcam.
"""

import logging
from typing import Optional, Tuple
import numpy as np
import os

# Set up logging
logger = logging.getLogger(__name__)

# Try to import OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    logger.warning(
        "OpenCV (cv2) is not installed. "
        "Install it with: pip install opencv-python-headless"
    )


class OpenCVCamera:
    """
    Camera class that uses OpenCV to capture images.
    
    This works with most USB webcams and is useful for testing
    on regular computers (not just Raspberry Pi).
    
    Usage:
        camera = OpenCVCamera()
        if camera.open():
            image = camera.capture()
            if image is not None:
                # Save or process the image
                pass
            camera.close()
    """
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize the camera.
        
        Args:
            camera_index: Which camera to use (0 = first camera, 1 = second, etc.)
        """
        self.camera_index = camera_index
        self.cap = None  # The OpenCV VideoCapture object
        self.resolution: Tuple[int, int] = (1280, 720)  # Width, Height
        self._is_open = False
    
    def is_available(self) -> bool:
        """Check if OpenCV is installed and working."""
        return OPENCV_AVAILABLE
    
    def open(self, width: int = 1280, height: int = 720) -> bool:
        """
        Open the camera and prepare it for capturing.
        
        Args:
            width: Desired image width in pixels
            height: Desired image height in pixels
            
        Returns:
            True if camera opened successfully, False otherwise
        """
        if not OPENCV_AVAILABLE:
            logger.error("OpenCV is not available. Cannot open camera.")
            return False
        
        try:
            # Suppress OpenCV's verbose warnings by redirecting stderr at OS level
            devnull = os.open(os.devnull, os.O_WRONLY)
            old_stderr_fd = os.dup(2)
            os.dup2(devnull, 2)
            os.close(devnull)
            
            try:
                # Try to open the camera
                # On Linux (like Raspberry Pi), we use V4L2 backend
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_V4L2)
                
                if not self.cap.isOpened():
                    # Fallback: try without specifying backend
                    self.cap = cv2.VideoCapture(self.camera_index)
                
                if not self.cap.isOpened():
                    # Camera not available - provide helpful error message
                    logger.warning(
                        f"No camera device found at index {self.camera_index}. "
                        f"Check that your camera is connected and not in use by another application. "
                        f"On Linux, you can check for cameras with: ls /dev/video*"
                    )
                    return False
                
                # Set the resolution
                # Note: The camera might not support the exact resolution requested
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                
                # Read back the actual resolution (might be different from requested)
                actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                self.resolution = (actual_width, actual_height)
                
                logger.info(
                    f"Camera opened successfully. Resolution: {actual_width}x{actual_height}"
                )
                
                # Warm up the camera by capturing a few frames
                # Some cameras need this to adjust brightness
                for _ in range(3):
                    self.cap.read()
                
                self._is_open = True
                return True
                
            finally:
                # Restore stderr
                os.dup2(old_stderr_fd, 2)
                os.close(old_stderr_fd)
            
        except Exception as e:
            logger.error(f"Error opening camera: {e}")
            return False
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture a single image from the camera.
        
        Returns:
            The captured image as a numpy array, or None if capture failed.
            The image is in BGR format (Blue, Green, Red) which OpenCV uses.
        """
        if not self._is_open or self.cap is None:
            logger.error("Camera is not open. Call open() first.")
            return None
        
        try:
            # Read a frame from the camera
            ret, frame = self.cap.read()
            
            if ret and frame is not None:
                logger.debug(f"Captured image: {frame.shape}")
                return frame
            else:
                logger.error("Failed to capture frame from camera")
                return None
                
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None
    
    def close(self) -> None:
        """
        Close the camera and release resources.
        
        Always call this when you're done with the camera!
        """
        if self.cap is not None:
            try:
                self.cap.release()
                logger.info("Camera closed")
            except Exception as e:
                logger.warning(f"Error closing camera: {e}")
        
        self.cap = None
        self._is_open = False
    
    def is_open(self) -> bool:
        """Check if the camera is currently open."""
        return self._is_open and self.cap is not None and self.cap.isOpened()
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get the current capture resolution (width, height)."""
        return self.resolution


def save_image(image: np.ndarray, filepath: str, quality: int = 95) -> bool:
    """
    Save an image to a file.
    
    Args:
        image: The image to save (numpy array from capture)
        filepath: Where to save the image (full path with extension)
        quality: JPEG quality (1-100, higher = better quality, larger file)
        
    Returns:
        True if saved successfully, False otherwise
    """
    if not OPENCV_AVAILABLE:
        logger.error("OpenCV is not available. Cannot save image.")
        return False
    
    if image is None:
        logger.error("Cannot save None image")
        return False
    
    try:
        # Set compression parameters based on file format
        if filepath.lower().endswith('.jpg') or filepath.lower().endswith('.jpeg'):
            params = [cv2.IMWRITE_JPEG_QUALITY, quality]
        elif filepath.lower().endswith('.png'):
            # PNG compression: 0 = no compression, 9 = maximum compression
            params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
        else:
            params = []
        
        success = cv2.imwrite(filepath, image, params)
        
        if success:
            logger.debug(f"Image saved to {filepath}")
        else:
            logger.error(f"Failed to save image to {filepath}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return False


def test_camera(camera_index: int = 0) -> bool:
    """
    Test if a camera is working.
    
    This is useful for troubleshooting camera issues.
    
    Args:
        camera_index: Which camera to test
        
    Returns:
        True if camera works, False otherwise
    """
    camera = OpenCVCamera(camera_index)
    
    if not camera.is_available():
        print("❌ OpenCV is not installed")
        return False
    
    print(f"Testing camera at index {camera_index}...")
    
    if not camera.open():
        print("❌ Could not open camera")
        return False
    
    print(f"✓ Camera opened (resolution: {camera.get_resolution()})")
    
    image = camera.capture()
    camera.close()
    
    if image is not None:
        print(f"✓ Captured test image (shape: {image.shape})")
        return True
    else:
        print("❌ Failed to capture image")
        return False

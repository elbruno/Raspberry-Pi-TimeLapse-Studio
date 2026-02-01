"""
camera_picamera2.py - Raspberry Pi Camera Implementation

This file implements camera capture using the picamera2 library,
which is the official library for Raspberry Pi Camera Modules.

picamera2 is pre-installed on newer Raspberry Pi OS images and provides
excellent performance with the Pi Camera.
"""

import logging
from typing import Optional, Tuple
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

# Try to import picamera2
try:
    from picamera2 import Picamera2
    PICAMERA2_AVAILABLE = True
except ImportError:
    PICAMERA2_AVAILABLE = False
    Picamera2 = None
    logger.info(
        "picamera2 is not installed. This is normal on non-Pi systems. "
        "On Raspberry Pi, install it with: sudo apt install python3-picamera2"
    )


class PiCamera2Camera:
    """
    Camera class that uses picamera2 for Raspberry Pi Camera Module.
    
    This is the recommended camera option for Raspberry Pi because it
    provides the best performance with official Pi cameras.
    
    Usage:
        camera = PiCamera2Camera()
        if camera.open():
            image = camera.capture()
            if image is not None:
                # Save or process the image
                pass
            camera.close()
    """
    
    def __init__(self):
        """Initialize the camera (but don't open it yet)."""
        self.camera = None
        self.resolution: Tuple[int, int] = (1280, 720)
        self._is_open = False
    
    def is_available(self) -> bool:
        """Check if picamera2 is installed and working."""
        return PICAMERA2_AVAILABLE
    
    def open(self, width: int = 1280, height: int = 720) -> bool:
        """
        Open the camera and prepare it for capturing.
        
        Args:
            width: Desired image width in pixels
            height: Desired image height in pixels
            
        Returns:
            True if camera opened successfully, False otherwise
        """
        if not PICAMERA2_AVAILABLE:
            logger.error(
                "picamera2 is not available. "
                "Either install it (sudo apt install python3-picamera2) "
                "or switch camera_mode to 'opencv' in config.yaml"
            )
            return False
        
        try:
            # Create the camera object
            self.camera = Picamera2()
            
            # Configure the camera for still images
            config = self.camera.create_still_configuration(
                main={"size": (width, height), "format": "RGB888"}
            )
            self.camera.configure(config)
            
            # Start the camera
            self.camera.start()
            
            self.resolution = (width, height)
            self._is_open = True
            
            logger.info(f"Pi Camera opened successfully. Resolution: {width}x{height}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening Pi Camera: {e}")
            self._suggest_fixes(e)
            return False
    
    def _suggest_fixes(self, error: Exception) -> None:
        """
        Print helpful suggestions based on common errors.
        
        Args:
            error: The exception that occurred
        """
        error_str = str(error).lower()
        
        if "no cameras" in error_str or "camera not found" in error_str:
            logger.info(
                "TIP: Camera not found. Try these steps:\n"
                "  1. Check that the camera ribbon cable is connected properly\n"
                "  2. Enable the camera in raspi-config\n"
                "  3. Reboot the Raspberry Pi\n"
                "  4. Try 'libcamera-hello' command to test the camera"
            )
        elif "permission" in error_str:
            logger.info(
                "TIP: Permission denied. Try adding your user to the video group:\n"
                "  sudo usermod -aG video $USER\n"
                "  Then log out and log back in."
            )
    
    def capture(self) -> Optional[np.ndarray]:
        """
        Capture a single image from the camera.
        
        Returns:
            The captured image as a numpy array (RGB format), or None if failed.
        """
        if not self._is_open or self.camera is None:
            logger.error("Camera is not open. Call open() first.")
            return None
        
        try:
            # Capture an image as a numpy array
            image = self.camera.capture_array()
            
            if image is not None:
                logger.debug(f"Captured image: {image.shape}")
                return image
            else:
                logger.error("Failed to capture frame from Pi Camera")
                return None
                
        except Exception as e:
            logger.error(f"Error capturing image: {e}")
            return None
    
    def close(self) -> None:
        """
        Close the camera and release resources.
        
        Always call this when you're done with the camera!
        """
        if self.camera is not None:
            try:
                self.camera.stop()
                self.camera.close()
                logger.info("Pi Camera closed")
            except Exception as e:
                logger.warning(f"Error closing Pi Camera: {e}")
        
        self.camera = None
        self._is_open = False
    
    def is_open(self) -> bool:
        """Check if the camera is currently open."""
        return self._is_open and self.camera is not None
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get the current capture resolution (width, height)."""
        return self.resolution


def test_camera() -> bool:
    """
    Test if the Pi Camera is working.
    
    Returns:
        True if camera works, False otherwise
    """
    camera = PiCamera2Camera()
    
    if not camera.is_available():
        print("❌ picamera2 is not installed")
        print("   On Raspberry Pi, install it with: sudo apt install python3-picamera2")
        return False
    
    print("Testing Pi Camera...")
    
    if not camera.open():
        print("❌ Could not open Pi Camera")
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

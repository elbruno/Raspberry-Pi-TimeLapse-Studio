"""
overlay.py - Image Overlay Functions

This file adds overlays (like timestamps) to captured images.
An overlay is text or graphics drawn on top of the image.

We use this to "burn in" the capture time onto each photo,
which is helpful when reviewing time-lapse sequences.
"""

import logging
from datetime import datetime
from typing import Tuple, Optional
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

# Try to import OpenCV and PIL (for text rendering)
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageDraw = None
    ImageFont = None


def add_timestamp_overlay(
    image: np.ndarray,
    timestamp: Optional[datetime] = None,
    position: str = "bottom-right",
    font_scale: float = 1.0,
    color: Tuple[int, int, int] = (255, 255, 255),
    background_color: Tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    """
    Add a timestamp text overlay to an image.
    
    This function draws the date and time on the image so you can
    see when each photo was taken.
    
    Args:
        image: The image to modify (numpy array)
        timestamp: When the photo was taken (uses current time if not provided)
        position: Where to put the timestamp:
            - "bottom-right" (default)
            - "bottom-left"
            - "top-right"
            - "top-left"
        font_scale: Size of the text (1.0 = normal, 2.0 = double size)
        color: Text color as (Blue, Green, Red) values 0-255
        background_color: Background color for text readability
        
    Returns:
        The image with the timestamp added
        
    Example:
        >>> image = camera.capture()
        >>> image_with_time = add_timestamp_overlay(image, position="bottom-right")
    """
    if not OPENCV_AVAILABLE:
        logger.warning("OpenCV not available - cannot add overlay")
        return image
    
    if image is None:
        logger.error("Cannot add overlay to None image")
        return image
    
    # Make a copy so we don't modify the original
    result = image.copy()
    
    # Get current time if not provided
    if timestamp is None:
        timestamp = datetime.now()
    
    # Format the timestamp text
    text = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    # Get image dimensions
    height, width = result.shape[:2]
    
    # Calculate font settings
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_thickness = max(1, int(2 * font_scale))
    
    # Get the size of the text
    (text_width, text_height), baseline = cv2.getTextSize(
        text, font, font_scale, font_thickness
    )
    
    # Calculate position based on setting
    padding = 10
    
    if position == "bottom-right":
        x = width - text_width - padding
        y = height - padding
    elif position == "bottom-left":
        x = padding
        y = height - padding
    elif position == "top-right":
        x = width - text_width - padding
        y = text_height + padding
    elif position == "top-left":
        x = padding
        y = text_height + padding
    else:
        # Default to bottom-right
        x = width - text_width - padding
        y = height - padding
    
    # Draw a background rectangle for readability
    rect_start = (x - 5, y - text_height - 5)
    rect_end = (x + text_width + 5, y + baseline + 5)
    
    # Draw semi-transparent background
    cv2.rectangle(result, rect_start, rect_end, background_color, -1)
    
    # Draw the text
    cv2.putText(
        result,
        text,
        (x, y),
        font,
        font_scale,
        color,
        font_thickness,
        cv2.LINE_AA,  # Anti-aliased text for smooth edges
    )
    
    return result


def add_text_overlay(
    image: np.ndarray,
    text: str,
    position: Tuple[int, int] = (10, 30),
    font_scale: float = 1.0,
    color: Tuple[int, int, int] = (255, 255, 255),
    with_background: bool = True,
) -> np.ndarray:
    """
    Add custom text to an image at a specific position.
    
    This is more flexible than add_timestamp_overlay() because you can
    put any text anywhere on the image.
    
    Args:
        image: The image to modify
        text: The text to display
        position: (x, y) coordinates for the text
        font_scale: Size of the text
        color: Text color as (B, G, R)
        with_background: Whether to add a dark background for readability
        
    Returns:
        The image with text added
    """
    if not OPENCV_AVAILABLE:
        logger.warning("OpenCV not available - cannot add overlay")
        return image
    
    if image is None:
        return image
    
    result = image.copy()
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_thickness = max(1, int(2 * font_scale))
    
    if with_background:
        # Get text size for background rectangle
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, font_thickness
        )
        
        x, y = position
        rect_start = (x - 5, y - text_height - 5)
        rect_end = (x + text_width + 5, y + baseline + 5)
        
        cv2.rectangle(result, rect_start, rect_end, (0, 0, 0), -1)
    
    cv2.putText(
        result,
        text,
        position,
        font,
        font_scale,
        color,
        font_thickness,
        cv2.LINE_AA,
    )
    
    return result


def add_session_info_overlay(
    image: np.ndarray,
    session_id: str,
    photo_number: int,
    total_photos: int = 0,
) -> np.ndarray:
    """
    Add session information overlay to an image.
    
    Shows the session ID and photo count at the top of the image.
    
    Args:
        image: The image to modify
        session_id: Current session identifier
        photo_number: Which photo this is (1, 2, 3, etc.)
        total_photos: Total photos captured so far
        
    Returns:
        The image with session info added
    """
    if image is None:
        return image
    
    # Create the info text
    if total_photos > 0:
        text = f"{session_id} | Photo #{photo_number} of {total_photos}"
    else:
        text = f"{session_id} | Photo #{photo_number}"
    
    return add_text_overlay(
        image,
        text,
        position=(10, 30),
        font_scale=0.6,
        color=(200, 200, 200),
    )

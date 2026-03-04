"""
utils.py - Utility Functions for PiTimeLapse Lab

This file contains helper functions that are used throughout the application.
These are small, reusable pieces of code that do common tasks.

Think of utilities like tools in a toolbox - each one does one specific job.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Optional

# Set up logging for this module
# Logging is like keeping a diary of what the program does
logger = logging.getLogger(__name__)


def get_timestamp_string(dt: Optional[datetime] = None, format_style: str = "filename") -> str:
    """
    Create a formatted timestamp string from a datetime object.
    
    This is used to create unique filenames and session IDs.
    
    Args:
        dt: The datetime to format. Uses current time if not provided.
        format_style: How to format the timestamp:
            - "filename": Safe for filenames (20240115_143022)
            - "display": Human-readable (2024-01-15 14:30:22)
            - "iso": ISO format (2024-01-15T14:30:22)
    
    Returns:
        A formatted timestamp string.
        
    Example:
        >>> get_timestamp_string(format_style="filename")
        "20240115_143022"
        >>> get_timestamp_string(format_style="display")
        "2024-01-15 14:30:22"
    """
    if dt is None:
        dt = datetime.now()
    
    if format_style == "filename":
        # Format safe for filenames (no colons or spaces)
        return dt.strftime("%Y%m%d_%H%M%S")
    elif format_style == "display":
        # Human-readable format
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    elif format_style == "iso":
        # ISO 8601 format (good for APIs and data exchange)
        return dt.isoformat()
    else:
        # Default to filename format
        return dt.strftime("%Y%m%d_%H%M%S")


def generate_session_id() -> str:
    """
    Generate a unique session ID based on current time.
    
    Session IDs look like: session_20240115_143022
    
    Returns:
        A unique session ID string.
    """
    timestamp = get_timestamp_string(format_style="filename")
    return f"session_{timestamp}"


def generate_image_filename(session_id: str, image_number: int, image_format: str = "jpg") -> str:
    """
    Generate a filename for a captured image.
    
    Filenames include a timestamp and sequence number so they sort correctly.
    
    Args:
        session_id: The current session's ID
        image_number: Which photo this is in the sequence (1, 2, 3, etc.)
        image_format: File extension (default: "jpg")
    
    Returns:
        A filename string like "img_001_20240115_143022.jpg"
        
    Example:
        >>> generate_image_filename("session_001", 5, "jpg")
        "img_005_20240115_143022.jpg"
    """
    timestamp = get_timestamp_string(format_style="filename")
    # Use zero-padded numbers so files sort correctly (001, 002, ... 010, 011)
    return f"img_{image_number:04d}_{timestamp}.{image_format}"


def format_duration(seconds: float) -> str:
    """
    Convert seconds into a human-readable duration string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        A string like "2h 15m 30s" or "5m 10s"
        
    Example:
        >>> format_duration(3661)
        "1h 1m 1s"
        >>> format_duration(125)
        "2m 5s"
    """
    if seconds < 0:
        return "0s"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0:  # Show minutes if there are hours
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_file_size(bytes_size: int) -> str:
    """
    Convert bytes to a human-readable file size.
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        A string like "1.5 MB" or "500 KB"
        
    Example:
        >>> format_file_size(1500000)
        "1.43 MB"
        >>> format_file_size(500)
        "500 B"
    """
    if bytes_size < 0:
        return "0 B"
    
    # Define size units (each is 1024 times bigger than the previous)
    units = ["B", "KB", "MB", "GB", "TB"]
    
    size = float(bytes_size)
    unit_index = 0
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    # Format with appropriate decimal places
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def get_folder_size_mb(folder_path: str) -> float:
    """
    Calculate the total size of all files in a folder in megabytes.
    
    This is used to check if we're running low on storage space.
    
    Args:
        folder_path: Path to the folder to measure
        
    Returns:
        Total size in megabytes (MB)
    """
    total_size = 0
    
    try:
        # os.walk goes through every file in every subfolder
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                # Only count if it's a file (not a folder)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
    except Exception as e:
        logger.warning(f"Could not calculate folder size: {e}")
        return 0.0
    
    # Convert bytes to megabytes
    return total_size / (1024 * 1024)


def ensure_folder_exists(folder_path: str) -> bool:
    """
    Make sure a folder exists, creating it if necessary.
    
    This is safer than just calling os.makedirs() because it handles
    the case where the folder already exists.
    
    Args:
        folder_path: Path to the folder to create
        
    Returns:
        True if the folder exists (or was created), False if there was an error.
    """
    try:
        os.makedirs(folder_path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Could not create folder '{folder_path}': {e}")
        return False


def is_valid_interval(interval: int) -> bool:
    """
    Check if a capture interval is valid.
    
    The interval must be a positive number and at least 1 second.
    Very short intervals (less than 1 second) could overwhelm the system.
    
    Args:
        interval: The interval in seconds to validate
        
    Returns:
        True if valid, False otherwise
    """
    return isinstance(interval, int) and interval >= 1


def clamp(value: float, min_value: float, max_value: float) -> float:
    """
    Restrict a value to be within a range.
    
    This is useful for making sure user input doesn't go beyond
    acceptable limits.
    
    Args:
        value: The value to clamp
        min_value: The minimum allowed value
        max_value: The maximum allowed value
        
    Returns:
        The clamped value
        
    Example:
        >>> clamp(150, 0, 100)
        100
        >>> clamp(-5, 0, 100)
        0
        >>> clamp(50, 0, 100)
        50
    """
    return max(min_value, min(max_value, value))

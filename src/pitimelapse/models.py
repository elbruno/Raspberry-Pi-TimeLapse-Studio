"""
models.py - Data Classes for PiTimeLapse Lab

This file defines simple data structures (called "dataclasses" in Python)
that hold information about:
- Sessions: A time-lapse recording session
- Status: The current state of the application

Think of dataclasses like forms or templates that organize related data together.

Example:
    session = Session(id="session_001", start_time=datetime.now())
    print(session.id)  # Output: session_001
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Session:
    """
    Represents a single time-lapse recording session.
    
    A session starts when you press "Start" and ends when you press "Stop"
    (or when the duration limit is reached).
    
    Attributes:
        id: A unique identifier for this session (like "session_20240115_143022")
        start_time: When the session started
        end_time: When the session ended (None if still running)
        interval_seconds: How many seconds between each photo
        output_folder: Where photos are saved on disk
        total_photos: How many photos have been captured
        errors: List of error messages that occurred during capture
        settings_used: A copy of the settings used for this session
    """
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    interval_seconds: int = 10
    output_folder: str = ""
    total_photos: int = 0
    errors: List[str] = field(default_factory=list)
    settings_used: dict = field(default_factory=dict)
    
    def is_active(self) -> bool:
        """Check if this session is still running (not ended yet)."""
        return self.end_time is None
    
    def duration_seconds(self) -> float:
        """
        Calculate how long the session has been running.
        
        Returns:
            Number of seconds the session has been active.
        """
        end = self.end_time if self.end_time else datetime.now()
        return (end - self.start_time).total_seconds()
    
    def to_dict(self) -> dict:
        """
        Convert this session to a dictionary (for JSON export).
        
        This is useful when saving session data to a file or
        sending it through the API.
        """
        return {
            "id": self.id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "interval_seconds": self.interval_seconds,
            "output_folder": self.output_folder,
            "total_photos": self.total_photos,
            "errors": self.errors,
            "settings_used": self.settings_used,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """
        Create a Session object from a dictionary.
        
        This is useful when loading session data from a JSON file.
        
        Args:
            data: A dictionary containing session information.
            
        Returns:
            A new Session object with the data filled in.
        """
        return cls(
            id=data.get("id", ""),
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else datetime.now(),
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            interval_seconds=data.get("interval_seconds", 10),
            output_folder=data.get("output_folder", ""),
            total_photos=data.get("total_photos", 0),
            errors=data.get("errors", []),
            settings_used=data.get("settings_used", {}),
        )


@dataclass
class Status:
    """
    Represents the current state of the time-lapse application.
    
    This is what gets shown on the main page of the web interface.
    
    Attributes:
        is_running: Whether a time-lapse is currently being captured
        current_session_id: ID of the active session (if any)
        last_capture_time: When the last photo was taken
        next_capture_time: When the next photo will be taken
        total_photos: Total photos in current session
        total_errors: Number of errors in current session
        last_error: Most recent error message (if any)
        camera_mode: Which camera system is in use (\"opencv\" by default, or \"picamera2\")
        camera_available: Whether the camera is working
    """
    is_running: bool = False
    current_session_id: Optional[str] = None
    last_capture_time: Optional[datetime] = None
    next_capture_time: Optional[datetime] = None
    total_photos: int = 0
    total_errors: int = 0
    last_error: Optional[str] = None
    camera_mode: str = "opencv"
    camera_available: bool = True
    
    def to_dict(self) -> dict:
        """
        Convert status to a dictionary for the API.
        
        This is sent as JSON to the web interface.
        """
        return {
            "is_running": self.is_running,
            "current_session_id": self.current_session_id,
            "last_capture_time": self.last_capture_time.isoformat() if self.last_capture_time else None,
            "next_capture_time": self.next_capture_time.isoformat() if self.next_capture_time else None,
            "total_photos": self.total_photos,
            "total_errors": self.total_errors,
            "last_error": self.last_error,
            "camera_mode": self.camera_mode,
            "camera_available": self.camera_available,
        }

"""
conftest.py - Shared fixtures for Touch TimeLapse tests.

Provides common mocks and fixtures used across test modules.
All hardware (cv2, psutil, pygame) is mocked for CI compatibility.
"""

import sys
import json
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path so we can import the app modules
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def sample_config():
    """A valid default configuration dict."""
    return {
        "camera": {
            "index": 0,
            "width": 1280,
            "height": 720,
        },
        "capture": {
            "interval_seconds": 30,
            "quality": 85,
            "max_photos": 0,
            "duration_minutes": 0,
        },
        "storage": {
            "base_path": "./data",
            "use_usb": True,
        },
    }


@pytest.fixture
def sample_frame():
    """A fake camera frame (640x480 BGR numpy array)."""
    return np.zeros((480, 640, 3), dtype=np.uint8)


@pytest.fixture
def mock_cv2():
    """Mock cv2 module with a functional VideoCapture."""
    mock = MagicMock()
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock.VideoCapture.return_value = mock_cap
    mock.imencode.return_value = (True, np.array([255, 216, 255], dtype=np.uint8))
    return mock


@pytest.fixture
def session_dict():
    """A sample session metadata dict."""
    return {
        "session_id": "session_20250101_120000",
        "start_time": "2025-01-01T12:00:00",
        "end_time": None,
        "total_photos": 5,
        "photo_paths": [f"photo_{i:06d}.jpg" for i in range(1, 6)],
        "errors": [],
        "status": "active",
    }

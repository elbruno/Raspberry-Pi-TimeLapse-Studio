"""
test_capture_engine.py - Tests for the background capture engine.

Tests CaptureEngine start/stop/status with mocked camera and storage.
Uses short intervals and threading for fast, CI-friendly tests.

To run:
    pytest tests/test_capture_engine.py -v
"""

import time
import threading
import pytest
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock


@pytest.fixture
def mock_camera():
    """A mock camera that returns frames."""
    camera = MagicMock()
    camera.is_available.return_value = True
    camera.open.return_value = True
    camera.capture.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
    camera.close.return_value = None
    return camera


@pytest.fixture
def mock_storage(tmp_path):
    """A mock StorageManager."""
    storage = MagicMock()
    storage.save_photo.return_value = str(tmp_path / "photo_000001.jpg")
    storage.save_session_metadata.return_value = None
    return storage


@pytest.fixture
def mock_session():
    """A mock session object."""
    session = MagicMock()
    session.session_id = "test_session"
    session.total_photos = 0
    session.photo_paths = []
    session.errors = []
    session.status = "active"
    return session


@pytest.fixture
def capture_config():
    """Config dict for capture engine with short interval."""
    return {
        "capture": {
            "interval_seconds": 0.1,  # Very short for testing
            "quality": 85,
            "max_photos": 0,
            "duration_minutes": 0,
            "retry_delay_seconds": 0.05,
        },
        "camera": {
            "index": 0,
            "width": 640,
            "height": 480,
        },
    }


class TestCaptureEngineStartStop:
    """Tests for engine lifecycle."""

    def test_start_begins_capture(self, mock_session, mock_camera, mock_storage, capture_config):
        """start() begins background capture thread."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        engine.start(mock_session, mock_camera, mock_storage, capture_config)

        try:
            assert engine.is_running is True
            # Give it time to capture at least one frame
            time.sleep(0.3)
            assert mock_camera.capture.called
        finally:
            engine.stop()

    def test_stop_ends_capture(self, mock_session, mock_camera, mock_storage, capture_config):
        """stop() cleanly stops the capture thread."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        engine.start(mock_session, mock_camera, mock_storage, capture_config)
        time.sleep(0.2)
        engine.stop()

        # Wait briefly for thread to finish
        time.sleep(0.2)
        assert engine.is_running is False

    def test_is_running_false_before_start(self):
        """is_running is False before start() is called."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        assert engine.is_running is False

    def test_double_stop_is_safe(self, mock_session, mock_camera, mock_storage, capture_config):
        """Calling stop() twice does not raise."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        engine.start(mock_session, mock_camera, mock_storage, capture_config)
        engine.stop()
        time.sleep(0.1)
        # Second stop should not crash
        engine.stop()


class TestCaptureEngineStatus:
    """Tests for status reporting."""

    def test_get_status_returns_dict(self, mock_session, mock_camera, mock_storage, capture_config):
        """get_status() returns a dict with expected keys."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        engine.start(mock_session, mock_camera, mock_storage, capture_config)

        try:
            status = engine.get_status()
            assert isinstance(status, dict)
            # Should contain at minimum these fields
            assert "is_running" in status or "running" in status
        finally:
            engine.stop()

    def test_get_status_before_start(self):
        """get_status() works even before start()."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        status = engine.get_status()

        assert isinstance(status, dict)


class TestCaptureEngineCapture:
    """Tests for the actual capture behavior."""

    def test_captures_photos_at_interval(self, mock_session, mock_camera, mock_storage, capture_config):
        """Engine captures photos at the configured interval."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        engine.start(mock_session, mock_camera, mock_storage, capture_config)

        try:
            # Wait long enough for multiple captures (interval=0.1s)
            time.sleep(0.5)
            assert mock_camera.capture.call_count >= 2
            assert mock_storage.save_photo.call_count >= 2
        finally:
            engine.stop()

    def test_retry_on_camera_failure(self, mock_session, mock_camera, mock_storage, capture_config):
        """Engine retries when camera.capture() returns None."""
        # First call fails, second succeeds
        mock_camera.capture.side_effect = [
            None,
            np.zeros((480, 640, 3), dtype=np.uint8),
            np.zeros((480, 640, 3), dtype=np.uint8),
        ]

        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        engine.start(mock_session, mock_camera, mock_storage, capture_config)

        try:
            time.sleep(0.5)
            # Camera should have been called multiple times (retries + normal captures)
            assert mock_camera.capture.call_count >= 2
        finally:
            engine.stop()

    def test_session_metadata_updated_after_capture(
        self, mock_session, mock_camera, mock_storage, capture_config
    ):
        """Session metadata is saved after each successful capture."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        engine.start(mock_session, mock_camera, mock_storage, capture_config)

        try:
            time.sleep(0.5)
            assert mock_storage.save_session_metadata.called
        finally:
            engine.stop()

    def test_stop_with_no_captures(self, mock_session, mock_camera, mock_storage, capture_config):
        """Engine can be stopped immediately without any captures."""
        from capture_engine import CaptureEngine

        engine = CaptureEngine()
        engine.start(mock_session, mock_camera, mock_storage, capture_config)
        engine.stop()
        time.sleep(0.1)

        assert engine.is_running is False

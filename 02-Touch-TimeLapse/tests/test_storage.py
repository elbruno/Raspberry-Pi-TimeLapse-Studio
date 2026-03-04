"""
test_storage.py - Tests for storage management and session handling.

Tests StorageManager and Session dataclass with tmp_path fixtures.
No real hardware required.

To run:
    pytest tests/test_storage.py -v
"""

import json
import os
import pytest
import numpy as np
from unittest.mock import patch, MagicMock


class TestCreateSession:
    """Tests for session creation."""

    def test_create_session_returns_session(self, tmp_path):
        """create_session() returns a Session with valid fields."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()

        assert session.session_id is not None
        assert session.start_time is not None
        assert session.end_time is None
        assert session.total_photos == 0
        assert session.photo_paths == []
        assert session.errors == []
        assert session.status == "active"

    def test_create_session_creates_folder(self, tmp_path):
        """create_session() creates a session folder on disk."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()

        session_dir = tmp_path / session.session_id
        assert session_dir.exists()
        assert session_dir.is_dir()

    def test_create_session_writes_metadata(self, tmp_path):
        """create_session() writes initial session.json."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()

        metadata_path = tmp_path / session.session_id / "session.json"
        assert metadata_path.exists()

        data = json.loads(metadata_path.read_text())
        assert data["session_id"] == session.session_id
        assert data["status"] == "active"

    def test_multiple_sessions_unique_ids(self, tmp_path):
        """Each session gets a unique ID."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        s1 = storage.create_session()
        s2 = storage.create_session()

        assert s1.session_id != s2.session_id


class TestSavePhoto:
    """Tests for photo saving."""

    @patch("storage_manager.cv2", create=True)
    def test_save_photo_returns_path(self, mock_cv2, tmp_path):
        """save_photo() returns the saved file path."""
        mock_cv2.imencode.return_value = (True, np.array([255, 216, 255], dtype=np.uint8))
        mock_cv2.imwrite = MagicMock(return_value=True)

        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        path = storage.save_photo(session, frame, quality=85)

        assert path is not None
        assert isinstance(path, str)
        assert path.endswith(".jpg")

    @patch("storage_manager.cv2", create=True)
    def test_save_photo_sequential_naming(self, mock_cv2, tmp_path):
        """Photos are named sequentially: photo_000001.jpg, photo_000002.jpg."""
        mock_cv2.imencode.return_value = (True, np.array([255], dtype=np.uint8))
        mock_cv2.imwrite = MagicMock(return_value=True)

        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        p1 = storage.save_photo(session, frame, quality=85)
        p2 = storage.save_photo(session, frame, quality=85)

        assert "000001" in p1
        assert "000002" in p2

    @patch("storage_manager.cv2", create=True)
    def test_save_photo_updates_session(self, mock_cv2, tmp_path):
        """save_photo() increments session.total_photos."""
        mock_cv2.imencode.return_value = (True, np.array([255], dtype=np.uint8))
        mock_cv2.imwrite = MagicMock(return_value=True)

        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        storage.save_photo(session, frame, quality=85)
        assert session.total_photos == 1

        storage.save_photo(session, frame, quality=85)
        assert session.total_photos == 2


class TestSessionMetadata:
    """Tests for metadata persistence."""

    def test_save_session_metadata_writes_json(self, tmp_path):
        """save_session_metadata() writes valid JSON to disk."""
        from storage_manager import StorageManager, Session

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()
        session.total_photos = 42
        session.status = "completed"

        storage.save_session_metadata(session)

        metadata_path = tmp_path / session.session_id / "session.json"
        data = json.loads(metadata_path.read_text())
        assert data["total_photos"] == 42
        assert data["status"] == "completed"

    def test_load_session_metadata_roundtrip(self, tmp_path):
        """Saved metadata can be loaded back with same values."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()
        session.total_photos = 10
        session.errors = ["test error"]
        storage.save_session_metadata(session)

        session_path = str(tmp_path / session.session_id)
        loaded = storage.load_session_metadata(session_path)

        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert loaded.total_photos == 10
        assert loaded.errors == ["test error"]

    def test_load_session_metadata_missing_returns_none(self, tmp_path):
        """load_session_metadata() returns None for nonexistent path."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        result = storage.load_session_metadata(str(tmp_path / "nonexistent"))

        assert result is None


class TestFindInterruptedSession:
    """Tests for session recovery."""

    def test_find_interrupted_session_detects_active(self, tmp_path):
        """Finds a session with status='active' and no end_time."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()
        # Session is active with no end_time by default
        storage.save_session_metadata(session)

        found = storage.find_interrupted_session()
        assert found is not None
        assert found.session_id == session.session_id
        assert found.status == "active"

    def test_find_interrupted_returns_none_when_all_completed(self, tmp_path):
        """Returns None when all sessions are completed."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()
        session.status = "completed"
        session.end_time = "2025-01-01T13:00:00"
        storage.save_session_metadata(session)

        found = storage.find_interrupted_session()
        assert found is None

    def test_find_interrupted_returns_none_when_empty(self, tmp_path):
        """Returns None when no sessions exist."""
        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        found = storage.find_interrupted_session()
        assert found is None


class TestResumeSession:
    """Tests for session resumption."""

    @patch("storage_manager.cv2", create=True)
    def test_resume_session_continues_numbering(self, mock_cv2, tmp_path):
        """Resumed session continues photo numbering from where it left off."""
        mock_cv2.imencode.return_value = (True, np.array([255], dtype=np.uint8))
        mock_cv2.imwrite = MagicMock(return_value=True)

        from storage_manager import StorageManager

        storage = StorageManager(str(tmp_path))
        session = storage.create_session()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

        # Capture 3 photos then "interrupt"
        for _ in range(3):
            storage.save_photo(session, frame, quality=85)
        storage.save_session_metadata(session)

        # Resume
        resumed = storage.resume_session(session)
        assert resumed.status == "active"
        assert resumed.total_photos == 3

        # Next photo should be #4
        p4 = storage.save_photo(resumed, frame, quality=85)
        assert "000004" in p4
        assert resumed.total_photos == 4

"""
test_storage.py - Tests for Storage Management

These tests check that our session storage and file management works correctly.

To run these tests:
    pytest tests/test_storage.py -v
"""

import os
import tempfile
import json
import pytest
from datetime import datetime, timedelta

# We need to add the src directory to the path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pitimelapse.storage import StorageManager
from pitimelapse.models import Session


class TestStorageManager:
    """Tests for the StorageManager class."""
    
    def test_init_creates_base_dir(self):
        """Test that initializing creates the base directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = os.path.join(tmpdir, "new_data")
            
            assert not os.path.exists(base_dir)
            
            storage = StorageManager(base_dir)
            
            assert os.path.exists(base_dir)
    
    def test_create_session_folder(self):
        """Test creating a new session folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            
            folder = storage.create_session_folder("test_session_001")
            
            assert os.path.exists(folder)
            assert "test_session_001" in folder
    
    def test_create_session_folder_auto_id(self):
        """Test creating a session folder with auto-generated ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            
            folder = storage.create_session_folder()
            
            assert os.path.exists(folder)
            assert "session_" in folder
    
    def test_save_and_load_session_metadata(self):
        """Test saving and loading session metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            folder = storage.create_session_folder("session_001")
            
            # Create a session
            session = Session(
                id="session_001",
                start_time=datetime.now(),
                interval_seconds=30,
                output_folder=folder,
                total_photos=10,
            )
            
            # Save it
            result = storage.save_session_metadata(session)
            assert result == True
            
            # Check that the file exists
            metadata_path = os.path.join(folder, "session.json")
            assert os.path.exists(metadata_path)
            
            # Load it back
            loaded = storage.load_session_metadata(folder)
            
            assert loaded is not None
            assert loaded.id == "session_001"
            assert loaded.interval_seconds == 30
            assert loaded.total_photos == 10
    
    def test_load_nonexistent_session(self):
        """Test loading a session that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            
            loaded = storage.load_session_metadata("/nonexistent/path")
            
            assert loaded is None
    
    def test_list_sessions(self):
        """Test listing all sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            
            # Create some sessions
            for i in range(3):
                folder = storage.create_session_folder(f"session_{i:03d}")
                session = Session(
                    id=f"session_{i:03d}",
                    start_time=datetime.now() - timedelta(hours=i),
                    output_folder=folder,
                    total_photos=i * 10,
                )
                storage.save_session_metadata(session)
            
            sessions = storage.list_sessions()
            
            assert len(sessions) == 3
            # Should be sorted by start time (newest first)
            assert sessions[0].id == "session_000"
    
    def test_list_sessions_empty(self):
        """Test listing sessions when there are none."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            
            sessions = storage.list_sessions()
            
            assert sessions == []
    
    def test_get_session_images(self):
        """Test getting images from a session folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            folder = storage.create_session_folder("session_001")
            
            # Create some dummy image files
            for i in range(5):
                filepath = os.path.join(folder, f"img_{i:04d}.jpg")
                with open(filepath, "w") as f:
                    f.write("dummy image data")
            
            # Also create a non-image file (should be ignored)
            with open(os.path.join(folder, "session.json"), "w") as f:
                f.write("{}")
            
            images = storage.get_session_images(folder)
            
            assert len(images) == 5
            assert all(img.endswith(".jpg") for img in images)
    
    def test_get_latest_images(self):
        """Test getting the most recent images."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            folder = storage.create_session_folder("session_001")
            
            # Create 20 image files
            for i in range(20):
                filepath = os.path.join(folder, f"img_{i:04d}.jpg")
                with open(filepath, "w") as f:
                    f.write("dummy " * 100)  # Give it some content
            
            # Get only the last 10
            latest = storage.get_latest_images(folder, count=10)
            
            assert len(latest) == 10
            # Should have image info
            assert "name" in latest[0]
            assert "size" in latest[0]
    
    def test_delete_session(self):
        """Test deleting a session."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            folder = storage.create_session_folder("session_to_delete")
            
            # Create some files
            with open(os.path.join(folder, "image.jpg"), "w") as f:
                f.write("dummy")
            
            assert os.path.exists(folder)
            
            result = storage.delete_session("session_to_delete")
            
            assert result == True
            assert not os.path.exists(folder)
    
    def test_delete_nonexistent_session(self):
        """Test deleting a session that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            
            result = storage.delete_session("nonexistent_session")
            
            assert result == False
    
    def test_cleanup_old_sessions(self):
        """Test cleaning up old sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            
            # Create an old session (8 days old)
            old_folder = storage.create_session_folder("session_old")
            old_session = Session(
                id="session_old",
                start_time=datetime.now() - timedelta(days=8),
                end_time=datetime.now() - timedelta(days=8),
                output_folder=old_folder,
            )
            storage.save_session_metadata(old_session)
            
            # Create a recent session (1 day old)
            recent_folder = storage.create_session_folder("session_recent")
            recent_session = Session(
                id="session_recent",
                start_time=datetime.now() - timedelta(days=1),
                end_time=datetime.now() - timedelta(days=1),
                output_folder=recent_folder,
            )
            storage.save_session_metadata(recent_session)
            
            # Cleanup sessions older than 7 days
            deleted = storage.cleanup_old_sessions(retention_days=7)
            
            assert deleted == 1
            assert not os.path.exists(old_folder)
            assert os.path.exists(recent_folder)
    
    def test_cleanup_zero_days_does_nothing(self):
        """Test that cleanup with 0 days doesn't delete anything."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            folder = storage.create_session_folder("session_001")
            
            old_session = Session(
                id="session_001",
                start_time=datetime.now() - timedelta(days=100),
                end_time=datetime.now() - timedelta(days=100),
                output_folder=folder,
            )
            storage.save_session_metadata(old_session)
            
            deleted = storage.cleanup_old_sessions(retention_days=0)
            
            assert deleted == 0
            assert os.path.exists(folder)


class TestSession:
    """Tests for the Session dataclass."""
    
    def test_is_active(self):
        """Test checking if a session is active."""
        active_session = Session(
            id="active",
            start_time=datetime.now(),
            end_time=None,
        )
        
        ended_session = Session(
            id="ended",
            start_time=datetime.now(),
            end_time=datetime.now(),
        )
        
        assert active_session.is_active() == True
        assert ended_session.is_active() == False
    
    def test_duration_seconds(self):
        """Test calculating session duration."""
        start = datetime.now() - timedelta(hours=1)
        end = datetime.now()
        
        session = Session(
            id="test",
            start_time=start,
            end_time=end,
        )
        
        duration = session.duration_seconds()
        
        # Should be about 3600 seconds (1 hour)
        assert 3590 < duration < 3610
    
    def test_to_dict(self):
        """Test converting session to dictionary."""
        session = Session(
            id="test_session",
            start_time=datetime(2024, 1, 15, 10, 0, 0),
            interval_seconds=30,
            total_photos=100,
        )
        
        data = session.to_dict()
        
        assert data["id"] == "test_session"
        assert data["interval_seconds"] == 30
        assert data["total_photos"] == 100
        assert "start_time" in data
    
    def test_from_dict(self):
        """Test creating session from dictionary."""
        data = {
            "id": "loaded_session",
            "start_time": "2024-01-15T10:00:00",
            "end_time": "2024-01-15T12:00:00",
            "interval_seconds": 60,
            "total_photos": 120,
        }
        
        session = Session.from_dict(data)
        
        assert session.id == "loaded_session"
        assert session.interval_seconds == 60
        assert session.total_photos == 120
        assert session.end_time is not None

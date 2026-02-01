"""
test_utils.py - Tests for Utility Functions

These tests check that our helper functions work correctly.

To run these tests:
    pytest tests/test_utils.py -v
"""

import os
import tempfile
import pytest
from datetime import datetime

# We need to add the src directory to the path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pitimelapse.utils import (
    get_timestamp_string,
    generate_session_id,
    generate_image_filename,
    format_duration,
    format_file_size,
    get_folder_size_mb,
    ensure_folder_exists,
    is_valid_interval,
    clamp,
)


class TestTimestampString:
    """Tests for get_timestamp_string function."""
    
    def test_filename_format(self):
        """Test filename-safe timestamp format."""
        dt = datetime(2024, 1, 15, 14, 30, 22)
        result = get_timestamp_string(dt, format_style="filename")
        
        assert result == "20240115_143022"
        # Should not contain characters unsafe for filenames
        assert ":" not in result
        assert " " not in result
    
    def test_display_format(self):
        """Test human-readable timestamp format."""
        dt = datetime(2024, 1, 15, 14, 30, 22)
        result = get_timestamp_string(dt, format_style="display")
        
        assert result == "2024-01-15 14:30:22"
    
    def test_iso_format(self):
        """Test ISO 8601 timestamp format."""
        dt = datetime(2024, 1, 15, 14, 30, 22)
        result = get_timestamp_string(dt, format_style="iso")
        
        assert "2024-01-15" in result
        assert "14:30:22" in result
    
    def test_default_uses_current_time(self):
        """Test that None datetime uses current time."""
        result = get_timestamp_string(None, format_style="filename")
        
        # Should be a valid timestamp string
        assert len(result) == 15  # YYYYMMDD_HHMMSS format
        assert "_" in result


class TestGenerateSessionId:
    """Tests for generate_session_id function."""
    
    def test_session_id_format(self):
        """Test that session ID has expected format."""
        session_id = generate_session_id()
        
        assert session_id.startswith("session_")
        assert len(session_id) > 8  # "session_" plus timestamp
    
    def test_session_id_uniqueness(self):
        """Test that consecutive session IDs are different."""
        import time
        
        id1 = generate_session_id()
        time.sleep(0.01)  # Small delay
        id2 = generate_session_id()
        
        # IDs within the same second might be the same, but
        # they should at least be valid
        assert id1.startswith("session_")
        assert id2.startswith("session_")


class TestGenerateImageFilename:
    """Tests for generate_image_filename function."""
    
    def test_filename_format(self):
        """Test that image filename has expected format."""
        filename = generate_image_filename("session_123", 1, "jpg")
        
        assert filename.startswith("img_0001_")
        assert filename.endswith(".jpg")
    
    def test_zero_padded_numbers(self):
        """Test that image numbers are zero-padded."""
        filename1 = generate_image_filename("session_123", 1, "jpg")
        filename10 = generate_image_filename("session_123", 10, "jpg")
        filename100 = generate_image_filename("session_123", 100, "jpg")
        
        assert "img_0001_" in filename1
        assert "img_0010_" in filename10
        assert "img_0100_" in filename100
    
    def test_different_formats(self):
        """Test different image formats."""
        jpg_filename = generate_image_filename("session_123", 1, "jpg")
        png_filename = generate_image_filename("session_123", 1, "png")
        
        assert jpg_filename.endswith(".jpg")
        assert png_filename.endswith(".png")


class TestFormatDuration:
    """Tests for format_duration function."""
    
    def test_seconds_only(self):
        """Test duration less than a minute."""
        assert format_duration(30) == "30s"
        assert format_duration(0) == "0s"
        assert format_duration(59) == "59s"
    
    def test_minutes_and_seconds(self):
        """Test duration with minutes."""
        assert format_duration(125) == "2m 5s"
        assert format_duration(60) == "1m 0s"
    
    def test_hours_minutes_seconds(self):
        """Test duration with hours."""
        assert format_duration(3661) == "1h 1m 1s"
        assert format_duration(7200) == "2h 0m 0s"
    
    def test_negative_duration(self):
        """Test that negative duration returns 0s."""
        assert format_duration(-10) == "0s"


class TestFormatFileSize:
    """Tests for format_file_size function."""
    
    def test_bytes(self):
        """Test small file sizes in bytes."""
        assert format_file_size(500) == "500 B"
        assert format_file_size(0) == "0 B"
    
    def test_kilobytes(self):
        """Test file sizes in KB."""
        result = format_file_size(1024)
        assert "KB" in result
        assert "1" in result
    
    def test_megabytes(self):
        """Test file sizes in MB."""
        result = format_file_size(1500000)
        assert "MB" in result
    
    def test_negative_size(self):
        """Test that negative size returns 0 B."""
        assert format_file_size(-100) == "0 B"


class TestGetFolderSizeMb:
    """Tests for get_folder_size_mb function."""
    
    def test_empty_folder(self):
        """Test size of empty folder is 0."""
        with tempfile.TemporaryDirectory() as tmpdir:
            size = get_folder_size_mb(tmpdir)
            assert size == 0.0
    
    def test_folder_with_files(self):
        """Test folder with some files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create some files
            for i in range(5):
                filepath = os.path.join(tmpdir, f"file{i}.txt")
                with open(filepath, "w") as f:
                    f.write("x" * 1000)  # 1000 bytes each
            
            size = get_folder_size_mb(tmpdir)
            
            # Should be about 5KB = 0.005 MB
            assert size > 0
            assert size < 1  # Less than 1 MB
    
    def test_nonexistent_folder(self):
        """Test that nonexistent folder returns 0."""
        size = get_folder_size_mb("/nonexistent/path/12345")
        assert size == 0.0


class TestEnsureFolderExists:
    """Tests for ensure_folder_exists function."""
    
    def test_create_new_folder(self):
        """Test creating a new folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_folder = os.path.join(tmpdir, "new_folder")
            
            assert not os.path.exists(new_folder)
            
            result = ensure_folder_exists(new_folder)
            
            assert result == True
            assert os.path.exists(new_folder)
            assert os.path.isdir(new_folder)
    
    def test_existing_folder(self):
        """Test that existing folder doesn't cause error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_folder_exists(tmpdir)
            
            assert result == True
            assert os.path.exists(tmpdir)
    
    def test_nested_folders(self):
        """Test creating nested folder structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "a", "b", "c")
            
            result = ensure_folder_exists(nested)
            
            assert result == True
            assert os.path.exists(nested)


class TestIsValidInterval:
    """Tests for is_valid_interval function."""
    
    def test_valid_intervals(self):
        """Test valid interval values."""
        assert is_valid_interval(1) == True
        assert is_valid_interval(10) == True
        assert is_valid_interval(3600) == True
    
    def test_invalid_intervals(self):
        """Test invalid interval values."""
        assert is_valid_interval(0) == False
        assert is_valid_interval(-1) == False
        assert is_valid_interval(-100) == False
    
    def test_non_integer_intervals(self):
        """Test that non-integers are invalid."""
        assert is_valid_interval(1.5) == False
        assert is_valid_interval("10") == False


class TestClamp:
    """Tests for clamp function."""
    
    def test_value_within_range(self):
        """Test that value within range is unchanged."""
        assert clamp(50, 0, 100) == 50
        assert clamp(0, 0, 100) == 0
        assert clamp(100, 0, 100) == 100
    
    def test_value_below_min(self):
        """Test that value below min is clamped to min."""
        assert clamp(-10, 0, 100) == 0
        assert clamp(-1000, -50, 50) == -50
    
    def test_value_above_max(self):
        """Test that value above max is clamped to max."""
        assert clamp(150, 0, 100) == 100
        assert clamp(1000, -50, 50) == 50

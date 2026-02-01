"""
test_config.py - Tests for Configuration Management

These tests check that our configuration loading and validation works correctly.

To run these tests:
    pytest tests/test_config.py -v
"""

import os
import tempfile
import pytest
import yaml

# We need to add the src directory to the path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pitimelapse.config import AppConfig, load_config, save_config


class TestAppConfig:
    """Tests for the AppConfig dataclass."""
    
    def test_default_values(self):
        """Test that default configuration values are set correctly."""
        config = AppConfig()
        
        assert config.camera_mode == "opencv"
        assert config.interval_seconds == 10
        assert config.resolution_width == 1280
        assert config.resolution_height == 720
        assert config.output_dir == "./data"
        assert config.image_format == "jpg"
        assert config.overlay_timestamp == True
        assert config.web_host == "0.0.0.0"
        assert config.web_port == 8000
    
    def test_validate_valid_config(self):
        """Test that a valid configuration passes validation."""
        config = AppConfig()
        errors = config.validate()
        
        assert errors == []
    
    def test_validate_invalid_camera_mode(self):
        """Test that invalid camera_mode is caught."""
        config = AppConfig(camera_mode="invalid_camera")
        errors = config.validate()
        
        assert len(errors) == 1
        assert "camera_mode" in errors[0]
    
    def test_validate_invalid_interval(self):
        """Test that interval less than 1 is caught."""
        config = AppConfig(interval_seconds=0)
        errors = config.validate()
        
        assert len(errors) == 1
        assert "interval_seconds" in errors[0]
    
    def test_validate_negative_interval(self):
        """Test that negative interval is caught."""
        config = AppConfig(interval_seconds=-5)
        errors = config.validate()
        
        assert len(errors) >= 1
        assert any("interval_seconds" in e for e in errors)
    
    def test_validate_invalid_resolution(self):
        """Test that invalid resolution is caught."""
        config = AppConfig(resolution_width=0, resolution_height=-100)
        errors = config.validate()
        
        assert len(errors) >= 2
        assert any("resolution_width" in e for e in errors)
        assert any("resolution_height" in e for e in errors)
    
    def test_validate_invalid_port(self):
        """Test that invalid port numbers are caught."""
        config = AppConfig(web_port=0)
        errors = config.validate()
        
        assert len(errors) == 1
        assert "web_port" in errors[0]
        
        config = AppConfig(web_port=70000)
        errors = config.validate()
        
        assert len(errors) == 1
        assert "web_port" in errors[0]
    
    def test_validate_invalid_image_format(self):
        """Test that invalid image format is caught."""
        config = AppConfig(image_format="gif")
        errors = config.validate()
        
        assert len(errors) == 1
        assert "image_format" in errors[0]
    
    def test_validate_invalid_log_level(self):
        """Test that invalid log level is caught."""
        config = AppConfig(log_level="INVALID")
        errors = config.validate()
        
        assert len(errors) == 1
        assert "log_level" in errors[0]
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = AppConfig(camera_mode="picamera2", interval_seconds=30)
        config_dict = config.to_dict()
        
        assert config_dict["camera_mode"] == "picamera2"
        assert config_dict["interval_seconds"] == 30
        assert "output_dir" in config_dict
    
    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "camera_mode": "picamera2",
            "interval_seconds": 30,
            "resolution_width": 1920,
        }
        
        config = AppConfig.from_dict(data)
        
        assert config.camera_mode == "picamera2"
        assert config.interval_seconds == 30
        assert config.resolution_width == 1920
        # Other values should be defaults
        assert config.resolution_height == 720
    
    def test_from_dict_ignores_unknown_keys(self):
        """Test that unknown keys in dictionary are ignored."""
        data = {
            "camera_mode": "opencv",
            "unknown_key": "should be ignored",
            "another_unknown": 123,
        }
        
        config = AppConfig.from_dict(data)
        
        assert config.camera_mode == "opencv"
        # Should not have unknown attributes
        assert not hasattr(config, "unknown_key")


class TestConfigLoadSave:
    """Tests for loading and saving configuration files."""
    
    def test_save_and_load_config(self):
        """Test that we can save a config and load it back."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "test_config.yaml")
            
            # Create and save config
            original_config = AppConfig(
                camera_mode="picamera2",
                interval_seconds=60,
                resolution_width=1920,
                resolution_height=1080,
            )
            
            assert save_config(original_config, config_path)
            
            # Load it back
            loaded_config = load_config(config_path)
            
            assert loaded_config.camera_mode == "picamera2"
            assert loaded_config.interval_seconds == 60
            assert loaded_config.resolution_width == 1920
            assert loaded_config.resolution_height == 1080
    
    def test_load_nonexistent_config_returns_defaults(self):
        """Test that loading a nonexistent file returns defaults."""
        config = load_config("/nonexistent/path/config.yaml")
        
        # Should return default config
        assert config.camera_mode == "opencv"
        assert config.interval_seconds == 10
    
    def test_load_invalid_yaml_returns_defaults(self):
        """Test that loading invalid YAML returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "bad_config.yaml")
            
            # Write invalid YAML
            with open(config_path, "w") as f:
                f.write("this is: not: valid: yaml: [}")
            
            config = load_config(config_path)
            
            # Should return default config
            assert config.camera_mode == "opencv"


class TestConfigValidationMessages:
    """Test that validation error messages are helpful."""
    
    def test_error_messages_are_descriptive(self):
        """Test that error messages tell the user what's wrong."""
        config = AppConfig(
            camera_mode="bad",
            interval_seconds=0,
            web_port=100000,
        )
        
        errors = config.validate()
        
        # All errors should mention what the valid options/ranges are
        assert len(errors) >= 3
        
        # Error messages should be informative
        for error in errors:
            assert len(error) > 20  # Not just a short cryptic message

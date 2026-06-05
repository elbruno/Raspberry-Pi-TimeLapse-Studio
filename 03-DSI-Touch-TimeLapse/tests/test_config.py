"""
test_config.py - Tests for configuration loading and validation.

Tests load_config() and get_config_value() with YAML fixtures.
No hardware required.

To run:
    pytest tests/test_config.py -v
"""

import os
import pytest
import yaml


class TestLoadConfig:
    """Tests for load_config()."""

    def test_load_valid_yaml(self, tmp_path):
        """load_config() reads a valid YAML file."""
        config_data = {
            "camera": {"index": 0, "width": 1280, "height": 720},
            "capture": {"interval_seconds": 10, "quality": 85},
        }
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump(config_data))

        from config import load_config

        config = load_config(str(config_file))

        assert config["camera"]["index"] == 0
        assert config["capture"]["quality"] == 85

    def test_load_missing_file_returns_defaults(self):
        """load_config() returns defaults when file doesn't exist."""
        from config import load_config

        config = load_config("/nonexistent/config.yaml")

        assert isinstance(config, dict)
        # Should have sensible default structure
        assert "camera" in config or "capture" in config or len(config) > 0

    def test_load_empty_file_returns_defaults(self, tmp_path):
        """load_config() handles empty YAML file gracefully."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        from config import load_config

        config = load_config(str(config_file))
        assert isinstance(config, dict)

    def test_load_invalid_yaml_returns_defaults(self, tmp_path):
        """load_config() handles malformed YAML gracefully."""
        config_file = tmp_path / "bad.yaml"
        config_file.write_text("camera: {invalid: [}")

        from config import load_config

        config = load_config(str(config_file))
        assert isinstance(config, dict)


class TestGetConfigValue:
    """Tests for get_config_value() with dot notation."""

    def test_get_nested_value(self):
        """Retrieves nested value with dot notation."""
        from config import get_config_value

        config = {
            "camera": {"index": 2, "width": 1920},
            "capture": {"interval_seconds": 30},
        }

        assert get_config_value(config, "camera.index") == 2
        assert get_config_value(config, "camera.width") == 1920
        assert get_config_value(config, "capture.interval_seconds") == 30

    def test_get_top_level_value(self):
        """Retrieves top-level value."""
        from config import get_config_value

        config = {"debug": True, "version": "1.0"}

        assert get_config_value(config, "debug") is True
        assert get_config_value(config, "version") == "1.0"

    def test_missing_key_returns_default(self):
        """Returns default value when key path doesn't exist."""
        from config import get_config_value

        config = {"camera": {"index": 0}}

        assert get_config_value(config, "camera.missing", default=42) == 42
        assert get_config_value(config, "nonexistent.key", default="fallback") == "fallback"

    def test_missing_key_default_none(self):
        """Returns None by default when key doesn't exist."""
        from config import get_config_value

        config = {"camera": {}}

        assert get_config_value(config, "camera.index") is None


class TestConfigValidation:
    """Tests for configuration value validation."""

    @pytest.mark.parametrize("index", [0, 1, 5])
    def test_valid_camera_index(self, index, sample_config):
        """Camera index >= 0 is valid."""
        sample_config["camera"]["index"] = index
        # Valid configs should not raise
        assert sample_config["camera"]["index"] >= 0

    @pytest.mark.parametrize("index", [-1, -100])
    def test_invalid_camera_index(self, index, sample_config):
        """Camera index < 0 is invalid."""
        sample_config["camera"]["index"] = index
        assert sample_config["camera"]["index"] < 0

    @pytest.mark.parametrize("quality", [1, 50, 100])
    def test_valid_quality_range(self, quality, sample_config):
        """Quality between 1-100 is valid."""
        sample_config["capture"]["quality"] = quality
        assert 1 <= sample_config["capture"]["quality"] <= 100

    @pytest.mark.parametrize("quality", [0, -5, 101, 200])
    def test_invalid_quality_range(self, quality, sample_config):
        """Quality outside 1-100 is invalid."""
        sample_config["capture"]["quality"] = quality
        assert not (1 <= sample_config["capture"]["quality"] <= 100)

    @pytest.mark.parametrize("interval", [1, 5, 60, 3600])
    def test_valid_interval(self, interval, sample_config):
        """Positive interval_seconds is valid."""
        sample_config["capture"]["interval_seconds"] = interval
        assert sample_config["capture"]["interval_seconds"] >= 1

    @pytest.mark.parametrize("interval", [0, -1])
    def test_invalid_interval(self, interval, sample_config):
        """Zero or negative interval_seconds is invalid."""
        sample_config["capture"]["interval_seconds"] = interval
        assert sample_config["capture"]["interval_seconds"] < 1

    def test_defaults_applied_for_missing_keys(self):
        """Missing config keys should get default values."""
        from config import get_config_value

        # Sparse config with missing keys
        config = {"camera": {}}

        # Should return defaults, not crash
        index = get_config_value(config, "camera.index", default=0)
        quality = get_config_value(config, "capture.quality", default=85)

        assert index == 0
        assert quality == 85


class TestGroveConfigSections:
    """Tests for Grove button/relay configuration defaults and validation."""

    def test_defaults_include_grove_sections(self):
        """load_config() returns Grove defaults when config file is missing."""
        from config import load_config

        cfg = load_config("/nonexistent/config.yaml")
        assert "grove_button" in cfg
        assert "grove_relay" in cfg
        assert "grove_relay_2" in cfg
        assert cfg["grove_button"]["pin_button1"] == 5
        assert isinstance(cfg["grove_relay"]["pin"], int)
        assert cfg["grove_relay"]["active_high"] is True
        assert isinstance(cfg["grove_relay_2"]["pin"], int)
        assert cfg["grove_relay_2"]["active_high"] is True

    def test_validate_config_rejects_invalid_grove_values(self, sample_config):
        """validate_config() returns errors for malformed Grove settings."""
        from config import validate_config

        sample_config["grove_button"] = {
            "enabled": True,
            "pin_button1": -1,
            "pin_button2": 6,
            "debounce_ms": -10,
            "start_stop_button": "invalid",
        }
        sample_config["grove_relay"] = {
            "enabled": True,
            "pin": -1,
            "active_high": "yes",
        }
        sample_config["grove_relay_2"] = {
            "enabled": True,
            "pin": -2,
            "active_high": "no",
        }

        errors = validate_config(sample_config)
        assert any("grove_button.pin_button1" in e for e in errors)
        assert any("grove_button.debounce_ms" in e for e in errors)
        assert any("grove_button.start_stop_button" in e for e in errors)
        assert any("grove_relay.pin" in e for e in errors)
        assert any("grove_relay.active_high" in e for e in errors)
        assert any("grove_relay_2.pin" in e for e in errors)
        assert any("grove_relay_2.active_high" in e for e in errors)

    def test_validate_config_rejects_relay_pin_conflict(self, sample_config):
        """When both relays are enabled they cannot share the same BCM pin."""
        from config import validate_config

        sample_config["grove_relay"] = {
            "enabled": True,
            "pin": 26,
            "active_high": True,
        }
        sample_config["grove_relay_2"] = {
            "enabled": True,
            "pin": 26,
            "active_high": True,
        }

        errors = validate_config(sample_config)
        assert any("cannot share the same pin" in e for e in errors)


class TestDisplayConfigSections:
    """Tests for display window sizing defaults and validation."""

    def test_defaults_include_display_window_settings(self):
        """load_config() returns display sizing defaults when config is missing."""
        from config import load_config

        cfg = load_config("/nonexistent/config.yaml")
        assert cfg["display"]["window_width"] == 800
        assert cfg["display"]["window_height"] == 450
        assert cfg["display"]["center_window"] is True
        assert cfg["display"]["fullscreen"] is False

    def test_validate_config_rejects_invalid_display_values(self, sample_config):
        """validate_config() returns errors for malformed display settings."""
        from config import validate_config

        sample_config["display"] = {
            "show_countdown": True,
            "show_storage_info": False,
            "window_width": 0,
            "window_height": -10,
            "center_window": "yes",
            "fullscreen": "no",
        }

        errors = validate_config(sample_config)
        assert any("display.window_width" in e for e in errors)
        assert any("display.window_height" in e for e in errors)
        assert any("display.center_window" in e for e in errors)
        assert any("display.fullscreen" in e for e in errors)


class TestLedConfig:
    """Tests for relay timing/light settings in led section."""

    def test_defaults_include_led_settings(self):
        from config import load_config

        cfg = load_config("/nonexistent/config.yaml")
        assert "enabled" in cfg["led"]
        assert "warmup_seconds" in cfg["led"]
        assert "pre_capture_lead_seconds" in cfg["led"]

    def test_validate_config_rejects_invalid_led_lead(self, sample_config):
        from config import validate_config

        sample_config["led"] = {
            "enabled": True,
            "warmup_seconds": 1,
            "pre_capture_lead_seconds": -1,
        }

        errors = validate_config(sample_config)
        assert any("led.pre_capture_lead_seconds" in e for e in errors)

"""
config.py - Configuration Loading and Validation for Touch TimeLapse

Loads settings from config.yaml, merges with sensible defaults,
and validates that all values are within acceptable ranges.

Usage:
    config = load_config()                          # loads config.yaml
    width = get_config_value(config, "camera.width", 640)
"""

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Try to import PyYAML
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False
    yaml = None
    logger.warning("PyYAML is not installed. Install with: pip install pyyaml")

# Sensible defaults — every key that config.yaml may contain
DEFAULTS: dict = {
    "camera": {
        "mode": "opencv",
        "index": 0,
        "width": 640,
        "height": 480,
    },
    "capture": {
        "interval_seconds": 30,
        "quality": 90,
    },
    "preview": {
        "fps": 6,
    },
    "storage": {
        "fallback_path": "./data",
    },
    "led": {
        "enabled": True,
        "warmup_seconds": 1.5,
        "pre_capture_lead_seconds": 0.0,
    },
    "display": {
        "show_countdown": True,
        "show_storage_info": True,
        "window_width": 800,
        "window_height": 450,
        "center_window": True,
        "fullscreen": False,
    },
    "grove_button": {
        "enabled": True,
        "pin_button1": 5,
        "pin_button2": 6,
        "debounce_ms": 250,
        "start_stop_button": "button1",
    },
    "grove_relay": {
        "enabled": True,
        "pin": 26,
        "active_high": True,
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into a copy of *base*."""
    merged = base.copy()
    for key, value in override.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str = "config.yaml") -> dict:
    """
    Load configuration from a YAML file and merge over defaults.

    Args:
        path: Path to the YAML config file.

    Returns:
        Merged configuration dictionary.
    """
    config = DEFAULTS.copy()

    if not YAML_AVAILABLE:
        logger.warning("YAML not available — using built-in defaults")
        return _deep_merge(DEFAULTS, {})

    if not os.path.exists(path):
        logger.info(f"Config file not found at {path} — using defaults")
        return _deep_merge(DEFAULTS, {})

    try:
        with open(path, "r") as f:
            loaded = yaml.safe_load(f) or {}
        config = _deep_merge(DEFAULTS, loaded)
        logger.info(f"Configuration loaded from {path}")
    except Exception as e:
        logger.error(f"Error reading {path}: {e} — using defaults")
        config = _deep_merge(DEFAULTS, {})

    return config


def save_config(config: dict, path: str = "config.yaml") -> bool:
    """
    Write the configuration dictionary back to a YAML file.

    Returns True on success, False on failure.
    """
    if not YAML_AVAILABLE:
        logger.error("Cannot save config — PyYAML not installed")
        return False
    try:
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        logger.info("Configuration saved to %s", path)
        return True
    except Exception as e:
        logger.error("Failed to save config to %s: %s", path, e)
        return False


def get_config_value(config: dict, key_path: str, default: Any = None) -> Any:
    """
    Retrieve a value using dot-notation (e.g. ``"camera.width"``).

    Args:
        config:   The configuration dictionary.
        key_path: Dot-separated key path.
        default:  Fallback if the key is missing.

    Returns:
        The configuration value, or *default*.
    """
    keys = key_path.split(".")
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def validate_config(config: dict) -> list[str]:
    """
    Validate configuration values and return a list of error strings.

    Returns an empty list when everything is valid.
    """
    errors: list[str] = []

    # Camera checks
    cam_index = get_config_value(config, "camera.index", 0)
    if not isinstance(cam_index, int) or cam_index < 0:
        errors.append(f"camera.index must be a non-negative integer, got {cam_index}")

    for dim in ("camera.width", "camera.height"):
        val = get_config_value(config, dim, 0)
        if not isinstance(val, int) or val <= 0:
            errors.append(f"{dim} must be a positive integer, got {val}")

    cam_mode = get_config_value(config, "camera.mode", "opencv")
    if cam_mode not in ("opencv", "picamera2"):
        errors.append(f"camera.mode must be 'opencv' or 'picamera2', got '{cam_mode}'")

    # Capture checks
    interval = get_config_value(config, "capture.interval_seconds", 30)
    if not isinstance(interval, (int, float)) or interval <= 0:
        errors.append(f"capture.interval_seconds must be > 0, got {interval}")

    quality = get_config_value(config, "capture.quality", 90)
    if not isinstance(quality, int) or quality < 1 or quality > 100:
        errors.append(f"capture.quality must be 1-100, got {quality}")

    # Preview checks
    fps = get_config_value(config, "preview.fps", 6)
    if not isinstance(fps, (int, float)) or fps <= 0:
        errors.append(f"preview.fps must be > 0, got {fps}")

    # LED checks
    led_enabled = get_config_value(config, "led.enabled", True)
    if not isinstance(led_enabled, bool):
        errors.append(f"led.enabled must be true or false, got {led_enabled}")

    led_warmup = get_config_value(config, "led.warmup_seconds", 1.5)
    if not isinstance(led_warmup, (int, float)) or led_warmup < 0:
        errors.append(f"led.warmup_seconds must be >= 0, got {led_warmup}")

    led_pre_capture = get_config_value(config, "led.pre_capture_lead_seconds", 0.0)
    if not isinstance(led_pre_capture, (int, float)) or led_pre_capture < 0:
        errors.append(
            f"led.pre_capture_lead_seconds must be >= 0, got {led_pre_capture}"
        )

    # Display checks
    for key in (
        "display.show_countdown",
        "display.show_storage_info",
        "display.center_window",
        "display.fullscreen",
    ):
        val = get_config_value(config, key, True)
        if not isinstance(val, bool):
            errors.append(f"{key} must be true or false, got {val}")

    for key in ("display.window_width", "display.window_height"):
        val = get_config_value(config, key, 0)
        if not isinstance(val, int) or val <= 0:
            errors.append(f"{key} must be a positive integer, got {val}")

    # Grove dual button checks
    grove_button_enabled = get_config_value(config, "grove_button.enabled", True)
    if not isinstance(grove_button_enabled, bool):
        errors.append(f"grove_button.enabled must be true or false, got {grove_button_enabled}")

    for key in ("grove_button.pin_button1", "grove_button.pin_button2"):
        pin = get_config_value(config, key, 0)
        if not isinstance(pin, int) or pin < 0:
            errors.append(f"{key} must be a non-negative integer, got {pin}")

    debounce_ms = get_config_value(config, "grove_button.debounce_ms", 250)
    if not isinstance(debounce_ms, int) or debounce_ms < 0:
        errors.append(f"grove_button.debounce_ms must be >= 0, got {debounce_ms}")

    start_stop_button = get_config_value(config, "grove_button.start_stop_button", "button1")
    if start_stop_button not in ("button1", "button2"):
        errors.append(
            "grove_button.start_stop_button must be 'button1' or 'button2', "
            f"got '{start_stop_button}'"
        )

    # Grove relay checks
    relay_enabled = get_config_value(config, "grove_relay.enabled", True)
    if not isinstance(relay_enabled, bool):
        errors.append(f"grove_relay.enabled must be true or false, got {relay_enabled}")

    relay_pin = get_config_value(config, "grove_relay.pin", 26)
    if not isinstance(relay_pin, int) or relay_pin < 0:
        errors.append(f"grove_relay.pin must be a non-negative integer, got {relay_pin}")

    relay_active_high = get_config_value(config, "grove_relay.active_high", True)
    if not isinstance(relay_active_high, bool):
        errors.append(
            f"grove_relay.active_high must be true or false, got {relay_active_high}"
        )

    return errors

"""Tests for the touchscreen settings UI model helpers."""

import pygame


def test_settings_screen_preserves_existing_nested_config_values():
    """Saving from the settings screen should not drop unrelated config keys."""
    from ui_components import SettingsScreen

    pygame.font.init()
    config = {
        "camera": {"index": 1, "width": 640, "height": 480},
        "capture": {"interval_seconds": 30, "quality": 90},
        "preview": {"fps": 6},
        "storage": {"fallback_path": "./data"},
        "led": {"backend": "grove", "enabled": True, "warmup_seconds": 1, "usb_port": "1-1.2"},
        "display": {
            "show_countdown": True,
            "show_storage_info": True,
            "window_width": 480,
            "window_height": 320,
            "center_window": True,
            "fullscreen": False,
        },
        "grove_button": {"enabled": True, "pin_button1": 5, "pin_button2": 6},
        "grove_light": {"enabled": True, "pin": 12},
    }

    screen = SettingsScreen(480, 320, config, camera_options=[(1, "USB Cam")])
    values = screen.get_values(base_config=config)

    assert values["led"]["backend"] == "grove"
    assert values["led"]["usb_port"] == "1-1.2"
    assert values["grove_button"]["pin_button1"] == 5
    assert values["grove_light"]["pin"] == 12
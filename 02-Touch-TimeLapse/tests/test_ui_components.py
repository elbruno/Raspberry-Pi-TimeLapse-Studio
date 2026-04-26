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
        "grove_button": {"enabled": True, "pin_button1": 5, "pin_button2": 6, "start_stop_button": "button2"},
        "grove_light": {"enabled": True, "pin": 12},
    }

    screen = SettingsScreen(480, 320, config, camera_options=[(1, "USB Cam")])
    values = screen.get_values(base_config=config)

    assert screen.tab_labels == ["Camera", "Display", "LED", "Buttons"]
    assert values["led"]["backend"] == "grove"
    assert values["led"]["usb_port"] == "1-1.2"
    assert values["grove_button"]["start_stop_button"] == "button2"
    assert values["grove_button"]["pin_button1"] == 5
    assert values["grove_light"]["pin"] == 12


def test_window_size_options_are_16_by_9_and_capped_to_display():
    """Display size presets should stay 16:9 and never exceed the actual screen."""
    from ui_components import SettingsScreen

    options, selected = SettingsScreen._build_window_size_options((1366, 768), (1280, 720))

    assert options
    assert all(w <= 1366 and h <= 768 for w, h in options)
    assert all(abs((w / h) - (16 / 9)) < 0.01 for w, h in options)
    assert options[selected] == (1280, 720)


def test_settings_screen_saves_selected_window_size_preset():
    """Saving should use the chosen preset pair, not independent width/height values."""
    from ui_components import SettingsScreen

    pygame.font.init()
    config = {
        "camera": {"index": 0, "width": 640, "height": 480},
        "capture": {"interval_seconds": 30, "quality": 90},
        "preview": {"fps": 6},
        "storage": {"fallback_path": "./data"},
        "led": {"backend": "grove", "enabled": True, "warmup_seconds": 1, "usb_port": "auto"},
        "display": {
            "show_countdown": True,
            "show_storage_info": True,
            "window_width": 560,
            "window_height": 400,
            "center_window": True,
            "fullscreen": False,
        },
        "grove_button": {"enabled": True, "pin_button1": 5, "pin_button2": 6},
        "grove_light": {"enabled": True, "pin": 12},
    }

    screen = SettingsScreen(
        560,
        400,
        config,
        camera_options=[(0, "USB Cam")],
        max_display_size=(1366, 768),
    )
    screen._window_size_selected = len(screen.window_size_options) - 1

    values = screen.get_values(base_config=config)
    selected_width, selected_height = screen.window_size_options[screen._window_size_selected]

    assert values["display"]["window_width"] == selected_width
    assert values["display"]["window_height"] == selected_height
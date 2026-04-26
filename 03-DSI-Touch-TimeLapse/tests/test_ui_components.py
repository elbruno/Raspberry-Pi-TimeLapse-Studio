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
        "grove_light": {
            "enabled": True,
            "pin": 12,
            "brightness": 64,
            "state_palette": "warm",
            "capture_flash_duration_ms": 120,
        },
    }

    screen = SettingsScreen(480, 320, config, camera_options=[(1, "USB Cam")])
    values = screen.get_values(base_config=config)

    assert screen.tab_labels == ["Camera", "Display", "LED", "Buttons"]
    assert values["led"]["backend"] == "grove"
    assert values["led"]["usb_port"] == "1-1.2"
    assert values["grove_button"]["start_stop_button"] == "button2"
    assert values["grove_button"]["pin_button1"] == 5
    assert values["grove_light"]["pin"] == 12
    assert values["grove_light"]["brightness"] == 64
    assert values["grove_light"]["state_palette"] == "warm"
    assert values["grove_light"]["capture_flash_duration_ms"] == 120


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


def test_window_size_options_keep_multiple_presets_when_windowed():
    """Even when SDL reports 640x360, App Size should still offer bigger presets."""
    from ui_components import SettingsScreen

    options, _ = SettingsScreen._build_window_size_options((640, 360), (640, 360))
    assert (640, 360) in options
    assert (800, 450) in options
    assert len(options) >= 2


def test_display_tab_app_size_next_cycles_option():
    """Tapping App Size next button should move to another preset."""
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
            "window_width": 640,
            "window_height": 360,
            "center_window": True,
            "fullscreen": False,
        },
        "grove_button": {"enabled": True, "pin_button1": 5, "pin_button2": 6},
        "grove_light": {"enabled": True, "pin": 12},
    }

    screen = SettingsScreen(640, 360, config, max_display_size=(640, 360))
    screen.active_tab = 1
    before = screen._window_size_selected
    screen.handle_tap(screen.window_size_btn_next.center)
    after = screen._window_size_selected

    assert len(screen.window_size_options) >= 2
    assert after != before


def test_camera_selector_is_below_quality_row():
    """Camera selector should not overlap interval/quality rows."""
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
            "window_width": 640,
            "window_height": 360,
            "center_window": True,
            "fullscreen": False,
        },
        "grove_button": {"enabled": True, "pin_button1": 5, "pin_button2": 6},
        "grove_light": {"enabled": True, "pin": 12},
    }

    screen = SettingsScreen(640, 360, config, camera_options=[(0, "USB Cam")])
    quality_bottom = screen.camera_rows[1].btn_plus.bottom

    assert screen.camera_btn_prev.y > quality_bottom


def test_led_tab_draws_hardware_message_without_crashing():
    """LED diagnostics should render feedback text so actions feel responsive."""
    from ui_components import SettingsScreen

    pygame.font.init()
    pygame.display.init()
    surface = pygame.Surface((640, 360))

    config = {
        "camera": {"index": 0, "width": 640, "height": 480},
        "capture": {"interval_seconds": 30, "quality": 90},
        "preview": {"fps": 6},
        "storage": {"fallback_path": "./data"},
        "led": {"backend": "grove", "enabled": True, "warmup_seconds": 1, "usb_port": "auto"},
        "display": {
            "show_countdown": True,
            "show_storage_info": True,
            "window_width": 640,
            "window_height": 360,
            "center_window": True,
            "fullscreen": False,
        },
        "grove_button": {"enabled": True, "pin_button1": 5, "pin_button2": 6},
        "grove_light": {"enabled": True, "pin": 12},
    }

    screen = SettingsScreen(640, 360, config)
    screen.active_tab = 2
    screen.set_hardware_message("Grove needs sudo", False)

    screen.draw(surface)

    pygame.display.quit()
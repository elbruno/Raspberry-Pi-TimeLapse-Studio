"""Focused tests for preview pause/resume helpers in timelapse_touch.py."""

from unittest.mock import MagicMock


def test_handle_settings_tap_routes_detect_actions():
    """Settings tap should dispatch detect camera/LED actions."""
    from timelapse_touch import TimeLapseApp

    app = TimeLapseApp.__new__(TimeLapseApp)
    app._settings_screen = MagicMock()
    app._save_settings = MagicMock()
    app._run_led_test = MagicMock()
    app._run_camera_detect = MagicMock()
    app._run_led_detect = MagicMock()
    app._set_preview_updates_enabled = MagicMock()
    app._screen_state = "settings"

    app._settings_screen.handle_tap.return_value = "detect_camera"
    TimeLapseApp._handle_settings_tap(app, (0, 0))
    app._run_camera_detect.assert_called_once()

    app._settings_screen.handle_tap.return_value = "detect_led"
    TimeLapseApp._handle_settings_tap(app, (0, 0))
    app._run_led_detect.assert_called_once()


def test_set_preview_updates_enabled_disables_and_joins_worker():
    """Disabling preview updates waits for the in-flight worker and clears cached state."""
    from timelapse_touch import TimeLapseApp

    app = TimeLapseApp.__new__(TimeLapseApp)
    app._preview_capture_timeout_s = 1.0
    app._preview_updates_enabled = True
    app._preview_capture_thread = MagicMock()
    app._preview_capture_thread.is_alive.return_value = False
    thread_mock = app._preview_capture_thread
    app._preview_capture_lock = MagicMock()
    app._preview_capture_result = object()
    app._preview_capture_ready = True
    app._last_preview_time = 123.0

    app._clear_preview_capture_state = TimeLapseApp._clear_preview_capture_state.__get__(app, TimeLapseApp)
    app._set_preview_updates_enabled = TimeLapseApp._set_preview_updates_enabled.__get__(app, TimeLapseApp)

    app._set_preview_updates_enabled(False, wait_for_thread=True)

    thread_mock.join.assert_called_once()
    assert app._preview_updates_enabled is False
    assert app._preview_capture_result is None
    assert app._preview_capture_ready is False
    assert app._preview_capture_thread is None


def test_set_preview_updates_enabled_resets_timer_when_reenabled():
    """Re-enabling preview refreshes should force an immediate fresh frame."""
    from timelapse_touch import TimeLapseApp

    app = TimeLapseApp.__new__(TimeLapseApp)
    app._preview_capture_timeout_s = 1.0
    app._preview_updates_enabled = False
    app._preview_capture_thread = None
    app._preview_capture_lock = MagicMock()
    app._preview_capture_result = None
    app._preview_capture_ready = False
    app._last_preview_time = 999.0

    app._clear_preview_capture_state = TimeLapseApp._clear_preview_capture_state.__get__(app, TimeLapseApp)
    app._set_preview_updates_enabled = TimeLapseApp._set_preview_updates_enabled.__get__(app, TimeLapseApp)

    app._set_preview_updates_enabled(True)

    assert app._preview_updates_enabled is True
    assert app._last_preview_time == 0.0
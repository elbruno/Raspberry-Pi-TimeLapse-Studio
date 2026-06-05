"""Focused tests for preview pause/resume helpers in timelapse_touch.py."""

import pytest
from unittest.mock import MagicMock

pytest.importorskip("pygame")


def _run_thread_target_immediately(monkeypatch):
    """Patch threading.Thread so start() runs target immediately (deterministic tests)."""
    import timelapse_touch as mod

    class _ImmediateThread:
        def __init__(self, target=None, name=None, daemon=None):
            self._target = target

        def start(self):
            if self._target:
                self._target()

    monkeypatch.setattr(mod.threading, "Thread", _ImmediateThread)


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


def test_run_led_detect_reports_sudo_message_when_grove_unavailable(monkeypatch):
    """Relay detect reports wiring/sudo guidance when controller detection fails."""
    from timelapse_touch import TimeLapseApp

    _run_thread_target_immediately(monkeypatch)

    app = TimeLapseApp.__new__(TimeLapseApp)
    app.config = {"grove_relay": {"pin": 26, "active_high": True}, "led": {"enabled": True}}
    app.led_detected = False
    app.led = None
    app.header = MagicMock()
    controller = MagicMock()
    controller.detect.return_value = False
    app.led_controller = controller

    app._settings_screen = MagicMock()

    TimeLapseApp._run_led_detect(app)

    app._settings_screen.set_hardware_message.assert_any_call(
        "Relay not detected (check wiring/sudo)", False
    )
    assert app.led_detected is False


def test_run_led_detect_initializes_controller_when_missing(monkeypatch):
    """If relay controller is None, detect should self-initialize before probing."""
    from timelapse_touch import TimeLapseApp
    import timelapse_touch as mod

    _run_thread_target_immediately(monkeypatch)

    app = TimeLapseApp.__new__(TimeLapseApp)
    app.config = {"grove_relay": {"pin": 26, "active_high": True}, "led": {"enabled": True}}
    app.led_detected = False
    app.led = None
    app.header = MagicMock()
    app._settings_screen = MagicMock()

    controller = MagicMock()
    controller.detect.return_value = True
    controller.port_name = "GPIO26"
    monkeypatch.setattr(mod, "LEDController", lambda pin, active_high: controller)
    app.led_controller = None

    TimeLapseApp._run_led_detect(app)

    assert app.led_controller is controller
    assert app.led is controller
    app._settings_screen.set_hardware_message.assert_any_call("Relay ✓ Detected!", True)


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


def test_enumerate_camera_candidates_keeps_secondary_stream_nodes(monkeypatch):
    """Camera probing should include non-primary stream nodes as fallback candidates."""
    from timelapse_touch import TimeLapseApp
    import timelapse_touch as mod

    app = TimeLapseApp.__new__(TimeLapseApp)

    fake_glob = [
        "/sys/class/video4linux/video0",
        "/sys/class/video4linux/video2",
    ]

    monkeypatch.setattr(mod.glob, "glob", lambda pattern: fake_glob)

    def _fake_exists(path):
        return path in {
            "/sys/class/video4linux/video0/name",
            "/sys/class/video4linux/video0/index",
            "/sys/class/video4linux/video2/name",
            "/sys/class/video4linux/video2/index",
        }

    monkeypatch.setattr(mod.os.path, "exists", _fake_exists)

    import builtins
    real_open = builtins.open

    class _FakeFile:
        def __init__(self, text):
            self._text = text

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self._text

    def _fake_open(path, mode="r", encoding=None):
        mapping = {
            "/sys/class/video4linux/video0/name": "USB Camera",
            "/sys/class/video4linux/video0/index": "0",
            "/sys/class/video4linux/video2/name": "USB Camera Secondary",
            "/sys/class/video4linux/video2/index": "1",
        }
        if path in mapping:
            return _FakeFile(mapping[path])
        return real_open(path, mode=mode, encoding=encoding)

    monkeypatch.setattr(builtins, "open", _fake_open)

    candidates = TimeLapseApp._enumerate_camera_candidates(app, configured_index=0)

    assert 0 in candidates
    assert 2 in candidates
    assert candidates.index(0) < candidates.index(2)
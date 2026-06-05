"""Tests for relay-based led_controller.py using mocked GPIO sysfs paths."""

from unittest.mock import MagicMock


def test_detect_returns_false_on_non_linux(monkeypatch):
    import led_controller as mod

    controller = mod.LEDController(pin=26, active_high=True)
    monkeypatch.setattr(mod.platform, "system", lambda: "Windows")
    assert controller.detect() is False


def test_turn_on_and_turn_off_write_expected_values():
    import led_controller as mod

    writes = []

    class FakeValuePath:
        def write_text(self, text, encoding="utf-8"):
            writes.append(text)

    controller = mod.LEDController(pin=26, active_high=True)
    controller._available = True
    controller._value_path = FakeValuePath()

    assert controller.turn_on() is True
    assert controller.turn_off() is True
    assert "1" in writes
    assert "0" in writes


def test_active_low_writes_inverted_values():
    import led_controller as mod

    writes = []

    class FakeValuePath:
        def write_text(self, text, encoding="utf-8"):
            writes.append(text)

    controller = mod.LEDController(pin=26, active_high=False)
    controller._available = True
    controller._value_path = FakeValuePath()

    controller.turn_on()
    controller.turn_off()

    assert writes[0] == "0"
    assert writes[1] == "1"
"""Tests for grove_dual_button.py without real GPIO hardware."""

from unittest.mock import MagicMock


def test_detect_returns_false_when_not_linux(monkeypatch):
    import grove_dual_button as mod

    monkeypatch.setattr(mod.platform, "system", lambda: "Windows")
    controller = mod.GroveDualButton()
    assert controller.detect() is False


def test_detect_and_poll_event(monkeypatch):
    import grove_dual_button as mod

    gpio = MagicMock()
    # Initial detect() reads HIGH for both buttons.
    # First poll reads button1 LOW edge and button2 HIGH.
    gpio.input.side_effect = [1, 1, 0, 1]

    monkeypatch.setattr(mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mod, "GPIO_AVAILABLE", True)
    monkeypatch.setattr(mod, "GPIO", gpio)

    controller = mod.GroveDualButton(pin_button1=5, pin_button2=6, debounce_ms=0)
    assert controller.detect() is True

    events = controller.poll_events()
    assert len(events) == 1
    assert events[0].button == "button1"

    controller.close()

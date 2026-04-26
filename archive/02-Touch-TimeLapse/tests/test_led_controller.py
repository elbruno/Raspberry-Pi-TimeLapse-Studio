"""Tests for led_controller.py without touching real USB hubs."""

from unittest.mock import MagicMock


def test_validate_explicit_port_parses_hub_and_port(monkeypatch):
    import led_controller as mod

    completed = MagicMock(returncode=0, stdout="Current status for hub 1-1 [0424:9514, 5 ports, ppps]\n  Port 2: 0100 power\n", stderr="")
    monkeypatch.setattr(mod, "_check_uhubctl", lambda: True)
    monkeypatch.setattr(mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mod.subprocess, "run", lambda *args, **kwargs: completed)

    controller = mod.LEDController("1-1.2")
    assert controller.detect() is True
    assert controller.port_name == "1-1.2"
    assert controller._hub_location == "1-1"
    assert controller._port_number == "2"


def test_turn_on_uses_explicit_hub_and_port(monkeypatch):
    import led_controller as mod

    calls = []

    def fake_run(cmd, capture_output=True, text=True, timeout=0):
        calls.append(cmd)
        if cmd == ["uhubctl"]:
            return MagicMock(returncode=0, stdout="Current status for hub 1-1 [0424:9514, 5 ports, ppps]\n  Port 2: 0100 power\n", stderr="")
        return MagicMock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(mod, "_check_uhubctl", lambda: True)
    monkeypatch.setattr(mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    controller = mod.LEDController("1-1.2")
    assert controller.detect() is True
    assert controller.turn_on() is True
    assert ["uhubctl", "-l", "1-1", "-p", "2", "-a", "on", "-r", "0"] in calls
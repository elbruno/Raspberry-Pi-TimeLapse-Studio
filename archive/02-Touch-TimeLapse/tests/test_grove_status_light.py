"""Tests for grove_status_light.py using mocked rpi_ws281x classes."""

from unittest.mock import MagicMock


def test_detect_returns_false_when_not_linux(monkeypatch):
    import grove_status_light as mod

    monkeypatch.setattr(mod.platform, "system", lambda: "Darwin")
    light = mod.GroveStatusLight()
    assert light.detect() is False


def test_detect_set_state_and_close(monkeypatch):
    import grove_status_light as mod

    strip = MagicMock()
    strip.numPixels.return_value = 3

    monkeypatch.setattr(mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mod, "WS281X_AVAILABLE", True)
    monkeypatch.setattr(mod, "PixelStrip", MagicMock(return_value=strip))
    monkeypatch.setattr(mod, "Color", lambda r, g, b: (r, g, b))

    light = mod.GroveStatusLight(pin=12, pixel_count=3, brightness=10)
    assert light.detect() is True

    light.set_state("capturing")
    assert strip.setPixelColor.call_count >= 3
    assert strip.show.call_count >= 1

    light.close()
    assert light.is_available() is False


def test_flash_test_restores_previous_state(monkeypatch):
    import grove_status_light as mod

    strip = MagicMock()
    strip.numPixels.return_value = 2

    monkeypatch.setattr(mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mod, "WS281X_AVAILABLE", True)
    monkeypatch.setattr(mod, "PixelStrip", MagicMock(return_value=strip))
    monkeypatch.setattr(mod, "Color", lambda r, g, b: (r, g, b))

    light = mod.GroveStatusLight(pin=12, pixel_count=2, brightness=10)
    assert light.detect() is True
    light.set_state("capturing")

    light.flash_test(0)

    assert light._last_state == "capturing"


def test_palette_and_capture_flash_defaults(monkeypatch):
    import grove_status_light as mod

    strip = MagicMock()
    strip.numPixels.return_value = 2

    monkeypatch.setattr(mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(mod, "WS281X_AVAILABLE", True)
    monkeypatch.setattr(mod, "PixelStrip", MagicMock(return_value=strip))
    monkeypatch.setattr(mod, "Color", lambda r, g, b: (r, g, b))

    light = mod.GroveStatusLight(
        pin=12,
        pixel_count=2,
        brightness=10,
        state_palette="high_contrast",
        capture_flash_duration_s=0.12,
    )
    assert light.detect() is True
    assert light.state_palette == "high_contrast"
    assert abs(light.capture_flash_duration_s - 0.12) < 0.001

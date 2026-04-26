"""Tests for the standalone LED option tester planning logic."""


def test_build_grove_trials_includes_current_and_common_fallbacks():
    from led_option_tester import build_grove_trials

    config = {
        "led": {"backend": "grove"},
        "grove_light": {
            "pin": 12,
            "pixel_count": 20,
            "brightness": 48,
            "state_palette": "warm",
        },
    }

    trials = build_grove_trials(config)

    assert trials
    assert trials[0].name == "Current config"
    assert trials[0].pin == 12
    assert trials[0].pixel_count == 20
    assert any(trial.pin == 18 for trial in trials)
    assert any(trial.pixel_count == 10 for trial in trials)
    assert any(trial.brightness == 255 for trial in trials)


def test_build_grove_trials_deduplicates_when_current_matches_fallback():
    from led_option_tester import build_grove_trials

    config = {
        "led": {"backend": "grove"},
        "grove_light": {
            "pin": 18,
            "pixel_count": 10,
            "brightness": 255,
            "state_palette": "high_contrast",
        },
    }

    trials = build_grove_trials(config)
    names = [trial.name for trial in trials]

    assert names.count("Current config") == 1
    assert len(trials) == len(set(trials))

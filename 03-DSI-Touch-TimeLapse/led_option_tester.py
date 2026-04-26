#!/usr/bin/env python3
"""Interactive diagnostic tool for finding a working Grove LED ring setup.

This script is intentionally separate from the main app so we can safely test
likely-good LED ring options without mutating ``config.yaml``.

It focuses on the Grove WS2813 ring/stick backend because the current Scenario 03
configuration uses ``led.backend: grove`` and ``grove_light.pixel_count: 20``.

Typical usage:
    python3 led_option_tester.py --list
    sudo python3 led_option_tester.py --interactive
    sudo python3 led_option_tester.py --auto --hold-seconds 2.0
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from config import load_config
from grove_status_light import GroveStatusLight, PALETTE_STATE_COLORS, WS281X_AVAILABLE


DEFAULT_RESULTS_FILE = "led_option_test_results.json"
KNOWN_PIXEL_COUNTS = (20, 10)
KNOWN_PINS = (12, 18)
KNOWN_PALETTES = ("classic", "high_contrast", "warm")
KNOWN_BRIGHTNESS = (32, 64, 128, 255)


@dataclass(frozen=True)
class GroveTrial:
    """One LED ring configuration to try."""

    name: str
    pin: int
    pixel_count: int
    brightness: int
    state_palette: str
    note: str = ""


@dataclass
class TrialResult:
    """Recorded outcome for one trial run."""

    index: int
    name: str
    pin: int
    pixel_count: int
    brightness: int
    state_palette: str
    detected: bool
    observed: str
    note: str = ""


def _ordered_unique(values: Iterable[int | str]) -> list[int | str]:
    seen: set[int | str] = set()
    ordered: list[int | str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def build_grove_trials(config: dict) -> list[GroveTrial]:
    """Build a small, practical set of ring/stick test combinations.

    The goal is not to brute-force every possible value. Instead, we try the
    combinations most likely to explain a "nothing lights up" report:

    - current config
    - brighter / higher contrast versions of the current config
    - alternate common PWM/data pin (BCM 18)
    - alternate common device size (10 pixels vs 20 pixels)
    """
    grove = config.get("grove_light", {})
    current_pin = int(grove.get("pin", 12))
    current_pixels = int(grove.get("pixel_count", 20))
    current_brightness = int(grove.get("brightness", 48))
    current_palette = str(grove.get("state_palette", "classic"))

    candidate_pins = [int(v) for v in _ordered_unique((current_pin, *KNOWN_PINS))]
    candidate_pixels = [int(v) for v in _ordered_unique((current_pixels, *KNOWN_PIXEL_COUNTS))]
    candidate_brightness = [int(v) for v in _ordered_unique((current_brightness, *KNOWN_BRIGHTNESS))]
    candidate_palettes = [str(v) for v in _ordered_unique((current_palette, *KNOWN_PALETTES))]

    trials: list[GroveTrial] = []

    def add_trial(name: str, pin: int, pixel_count: int, brightness: int, palette: str, note: str = "") -> None:
        trial = GroveTrial(name, pin, pixel_count, max(0, min(255, brightness)), palette, note)
        if trial not in trials:
            trials.append(trial)

    add_trial(
        "Current config",
        current_pin,
        current_pixels,
        current_brightness,
        current_palette,
        "Baseline from config.yaml",
    )
    add_trial(
        "Current pin + brighter classic",
        current_pin,
        current_pixels,
        max(current_brightness, 64),
        "classic",
        "Same wiring, classic palette, slightly brighter",
    )
    add_trial(
        "Current pin + high contrast",
        current_pin,
        current_pixels,
        max(current_brightness, 128),
        "high_contrast",
        "Best visibility while keeping current pin/pixel count",
    )
    add_trial(
        "Current pin + max brightness",
        current_pin,
        current_pixels,
        255,
        "high_contrast",
        "If this looks off too, the issue is likely wiring/pin/permissions",
    )

    for pin in candidate_pins:
        if pin != current_pin:
            add_trial(
                f"Alternate pin {pin}",
                pin,
                current_pixels,
                max(current_brightness, 128),
                "high_contrast",
                "Tests the other common WS281x-capable pin",
            )
            break

    for pixel_count in candidate_pixels:
        if pixel_count != current_pixels:
            add_trial(
                f"Alternate pixel count {pixel_count}",
                current_pin,
                pixel_count,
                max(current_brightness, 128),
                "high_contrast",
                "Switches between Grove stick (10) and ring (20)",
            )
            break

    for pin in candidate_pins:
        for pixel_count in candidate_pixels:
            if pin == current_pin and pixel_count == current_pixels:
                continue
            add_trial(
                f"Fallback combo pin {pin} / {pixel_count} px",
                pin,
                pixel_count,
                255,
                candidate_palettes[1] if len(candidate_palettes) > 1 else "high_contrast",
                "Last-resort bright combo across common hardware presets",
            )
            return trials

    return trials


def describe_supported_options(config: dict) -> dict:
    """Return a serializable summary of supported LED settings."""
    current = config.get("grove_light", {})
    return {
        "platform": platform.system(),
        "python": sys.version.split()[0],
        "running_as_root": os.geteuid() == 0 if hasattr(os, "geteuid") else False,
        "rpi_ws281x_available": WS281X_AVAILABLE,
        "configured_backend": config.get("led", {}).get("backend", "usb"),
        "current_grove_light": {
            "enabled": bool(current.get("enabled", True)),
            "pin": int(current.get("pin", 12)),
            "pixel_count": int(current.get("pixel_count", 20)),
            "brightness": int(current.get("brightness", 48)),
            "state_palette": str(current.get("state_palette", "classic")),
            "capture_flash_duration_ms": int(current.get("capture_flash_duration_ms", 80)),
        },
        "supported_options": {
            "led.backend": ["usb", "grove"],
            "grove_light.pin_common_values": list(KNOWN_PINS),
            "grove_light.pixel_count_common_values": list(KNOWN_PIXEL_COUNTS),
            "grove_light.brightness_range": [0, 255],
            "grove_light.brightness_suggested_test_values": list(KNOWN_BRIGHTNESS),
            "grove_light.state_palette": list(PALETTE_STATE_COLORS.keys()),
        },
    }


def print_trial_list(trials: list[GroveTrial]) -> None:
    """Show the planned trial sequence."""
    print("\nPlanned Grove LED trials:")
    for idx, trial in enumerate(trials, start=1):
        print(
            f"  {idx}. {trial.name}: pin={trial.pin}, pixels={trial.pixel_count}, "
            f"brightness={trial.brightness}, palette={trial.state_palette}"
        )
        if trial.note:
            print(f"     ↳ {trial.note}")


def run_trial(trial: GroveTrial, state_hold_seconds: float) -> bool:
    """Run one configuration and show a few easy-to-recognize light states."""
    light = GroveStatusLight(
        pin=trial.pin,
        pixel_count=trial.pixel_count,
        brightness=trial.brightness,
        state_palette=trial.state_palette,
        capture_flash_duration_s=0.20,
    )

    detected = light.detect()
    if not detected:
        print("    Result: detect() failed (no accessible LED output for this setup)")
        light.close()
        return False

    try:
        for state in ("idle", "capturing", "stopped", "error"):
            print(f"    Showing state: {state}")
            light.set_state(state)
            time.sleep(state_hold_seconds)
        print("    Showing bright flash test")
        light.flash_test(max(0.4, state_hold_seconds))
        time.sleep(0.15)
        light.set_state("off")
    finally:
        light.close()
    return True


def save_results(results_path: Path, summary: dict, results: list[TrialResult]) -> None:
    """Persist trial metadata so the chosen option is easy to trace later."""
    payload = {
        "summary": summary,
        "results": [asdict(item) for item in results],
        "saved_at_epoch": time.time(),
    }
    results_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Grove LED ring/stick configuration combinations.")
    parser.add_argument("--list", action="store_true", help="Only print detected options and planned trials.")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Pause between trials and ask whether the LEDs were visibly ON.",
    )
    parser.add_argument(
        "--auto",
        action="store_true",
        help="Run all trials without prompting; useful when you just want to watch the ring.",
    )
    parser.add_argument(
        "--hold-seconds",
        type=float,
        default=0.7,
        help="How long to hold each named state during a trial.",
    )
    parser.add_argument(
        "--results-file",
        default=DEFAULT_RESULTS_FILE,
        help="Where to save the observed outcomes.",
    )
    args = parser.parse_args()

    if not args.list and not args.auto and not args.interactive:
        args.interactive = True

    config = load_config("config.yaml")
    summary = describe_supported_options(config)
    trials = build_grove_trials(config)

    print("LED option tester — Grove ring/stick focus")
    print(json.dumps(summary, indent=2))
    print_trial_list(trials)

    if summary["configured_backend"] != "grove":
        print("\nWarning: config.yaml is not currently using the Grove backend.")
    if not summary["rpi_ws281x_available"]:
        print("\nWarning: rpi_ws281x is not installed/importable, so Grove tests will fail until that is fixed.")
    if not summary["running_as_root"]:
        print("\nWarning: you are not running as root. Grove WS281x output often requires sudo on Raspberry Pi.")

    if args.list:
        return 0

    results_path = Path(args.results_file)
    results: list[TrialResult] = []

    print("\nInstructions:")
    print("  - Watch the LED ring during each trial.")
    print("  - In interactive mode, answer whether you saw light.")
    print("  - Results are saved so we can pick the best config afterward.\n")

    try:
        for idx, trial in enumerate(trials, start=1):
            print(f"\n=== Trial {idx}/{len(trials)}: {trial.name} ===")
            print(
                f"pin={trial.pin}, pixels={trial.pixel_count}, "
                f"brightness={trial.brightness}, palette={trial.state_palette}"
            )
            detected = run_trial(trial, max(0.2, args.hold_seconds))
            observed = "pending"

            if args.interactive:
                while True:
                    answer = input("    Did you see any LEDs turn ON? [y/n/s/q]: ").strip().lower()
                    if answer in {"y", "yes"}:
                        observed = "on"
                        break
                    if answer in {"n", "no"}:
                        observed = "off"
                        break
                    if answer in {"s", "skip"}:
                        observed = "skipped"
                        break
                    if answer in {"q", "quit"}:
                        observed = "quit"
                        results.append(
                            TrialResult(
                                index=idx,
                                name=trial.name,
                                pin=trial.pin,
                                pixel_count=trial.pixel_count,
                                brightness=trial.brightness,
                                state_palette=trial.state_palette,
                                detected=detected,
                                observed=observed,
                                note=trial.note,
                            )
                        )
                        save_results(results_path, summary, results)
                        print(f"\nSaved partial results to {results_path}")
                        return 0
                    print("    Please answer y, n, s, or q.")
            else:
                observed = "unattended"

            results.append(
                TrialResult(
                    index=idx,
                    name=trial.name,
                    pin=trial.pin,
                    pixel_count=trial.pixel_count,
                    brightness=trial.brightness,
                    state_palette=trial.state_palette,
                    detected=detected,
                    observed=observed,
                    note=trial.note,
                )
            )
            save_results(results_path, summary, results)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        save_results(results_path, summary, results)
        print(f"Saved partial results to {results_path}")
        return 130

    print(f"\nFinished. Results saved to {results_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

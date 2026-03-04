# LED Controller Rewrite: Serial Relay → USB Port Power Control

**By:** Linguini (Backend Dev)  
**Date:** 2026-03-05

## Decision

Rewrote `02-Touch-TimeLapse/led_controller.py` to control USB LED lights by toggling USB port power instead of sending serial relay commands.

### Changes Made

1. **Complete rewrite of led_controller.py**
   - Removed pyserial dependency and LCUS-1 protocol commands
   - Added uhubctl-based USB port power control (Linux only)
   - Auto-detection skips system devices (cameras, storage, HID)
   - Explicit port configuration via `led.usb_port` in config.yaml

2. **Config updates**
   - Added `led.usb_port: "auto"` to config.py defaults
   - Documented usb_port option in config.yaml

3. **Interface preserved**
   - All public methods unchanged: `detect()`, `turn_on()`, `turn_off()`, `close()`, `is_available()`, `port_name`
   - `__init__()` now accepts optional `usb_port` parameter with default "auto"
   - Backward compatible with existing code (timelapse_touch.py, capture_engine.py)

## Problem

The original serial relay approach (LCUS-1 protocol via pyserial) didn't work — the USB LED stayed always on regardless of commands sent. User has a simple USB-powered LED that just needs power on/off, no special protocol.

## Technical Approach

### uhubctl Integration

Uses the `uhubctl` tool to control per-port USB power:
- `uhubctl -l {hub} -p {port} -a on -r 0` — turn port on
- `uhubctl -l {hub} -p {port} -a off -r 0` — turn port off
- `-r 0` disables port scanning/retry for faster execution

### Auto-Detection Logic

1. Check if uhubctl is installed (`uhubctl --version`)
2. Run `uhubctl` to list all hubs and ports with power switching
3. Parse output with regex to find hub locations and port numbers
4. **Skip ports with system devices** (USB hubs, mass storage, cameras, video, input/HID, audio)
5. Build candidate list of controllable ports with devices
6. Pick first candidate, or use explicit `led.usb_port` from config

### Platform Support

- **Linux only** — uhubctl primarily works on Raspberry Pi
- Gracefully returns False on Windows/macOS (platform.system() check)
- Logs helpful info message on non-Linux platforms

### Permissions

uhubctl typically requires root access. Options documented in code:
1. Run with sudo (simplest for dedicated Pi)
2. Add udev rule for non-root access
3. Use setuid/capabilities

Code detects "permission denied" errors and logs actionable message.

## Rationale

- User-reported issue: serial relay commands don't work
- Simple USB LED only needs power control, not protocol commands
- uhubctl is standard on Raspberry Pi (`sudo apt install uhubctl`)
- USB port power control is the "native" way to control power on Pi
- Keeps same interface so no other files need changes (Colette working on timelapse_touch.py)

## Impact

- **No changes needed** to timelapse_touch.py, capture_engine.py, or ui_components.py
- Existing code continues to work (backward compatible __init__ signature)
- Future improvement: pass `config["led"]["usb_port"]` when creating LEDController in timelapse_touch.py (currently uses default "auto")
- User must install uhubctl: `sudo apt install uhubctl`
- May need to run with sudo or configure udev rules for non-root access

## Testing Notes

- Tested interface compatibility (all methods present with correct signatures)
- Regex patterns tested with uhubctl output format (Pi 4 format)
- Platform detection tested (Linux vs Windows)
- Auto-detection skip logic prevents toggling camera/storage ports
- Permission error detection logs actionable message

## Future Enhancements

1. Add sysfs fallback for hubs without uhubctl support (use `/sys/bus/usb/devices/{busid}/authorized`)
2. Support hub-specific udev rules for non-root access
3. Cache uhubctl output to avoid re-scanning on every detect() call
4. Add unit tests for regex parsing with sample uhubctl outputs

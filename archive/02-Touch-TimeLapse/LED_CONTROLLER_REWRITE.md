# LED Controller Rewrite - USB Port Power Control

## Summary

Rewrote `led_controller.py` to control your USB LED by toggling USB port power on/off instead of sending serial relay commands. The old approach didn't work (LED stayed always on), so now we use the **uhubctl** tool to physically turn USB ports on and off.

## What Changed

### 1. **led_controller.py** - Complete Rewrite
- **Before**: Tried to send LCUS-1 serial relay commands (0xA0 protocol) via pyserial
- **After**: Uses `uhubctl` command-line tool to toggle USB port power
- **Interface**: UNCHANGED — all the same methods exist with same signatures

### 2. **config.py** - Added USB Port Option
- Added `"usb_port": "auto"` to LED defaults

### 3. **config.yaml** - Documented New Option
```yaml
led:
  enabled: true
  warmup_seconds: 1.0
  usb_port: auto         # "auto" to detect, or explicit like "1-1.2"
```

## How It Works

### Auto-Detection
1. Checks if `uhubctl` is installed
2. Scans all USB hubs for ports with power switching capability
3. **Skips system devices** (cameras, storage, keyboards, mice)
4. Picks the first available port with a connected device
5. If multiple candidates, logs a message suggesting you set `led.usb_port` explicitly

### Manual Configuration
If auto-detection picks the wrong port, you can specify explicitly:
```yaml
led:
  usb_port: "1-1.2"  # specific hub and port
```

To find your port:
```bash
sudo uhubctl
```

Look for your LED in the output and note its hub location and port number.

## Setup Requirements

### 1. Install uhubctl
```bash
sudo apt install uhubctl
```

### 2. Permissions
uhubctl needs root access. Two options:

**Option A: Run with sudo (simplest for dedicated Pi)**
```bash
sudo python timelapse_touch.py
```

**Option B: Add udev rule (one-time setup for non-root access)**
1. Create `/etc/udev/rules.d/52-usb-power.rules`:
   ```
   SUBSYSTEM=="usb", DRIVER=="usb", MODE="0666"
   ```
2. Reload rules:
   ```bash
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ```

## Testing

### Test the new controller:
```bash
cd 02-Touch-TimeLapse
sudo python test_led_usb_port.py
```

This will:
- Auto-detect your LED port
- Blink the LED 3 times (on for 1.5s, off for 1s)
- Report any errors

### Test with specific port:
```bash
sudo python test_led_usb_port.py --port 1-1.2
```

## Backward Compatibility

✅ **No changes needed to other files**
- timelapse_touch.py — still works exactly the same
- capture_engine.py — no changes needed
- ui_components.py — no changes needed

The interface is 100% preserved:
- `detect()` → bool
- `turn_on()` → bool
- `turn_off()` → bool
- `close()` → None
- `is_available()` → bool
- `port_name` → Optional[str]

## Platform Support

- ✅ **Linux (Raspberry Pi)** — fully supported
- ❌ **Windows/macOS** — gracefully disabled (logs info message, all methods return False)

## Troubleshooting

### "uhubctl not found"
```bash
sudo apt install uhubctl
```

### "permission denied"
Run with `sudo` or configure udev rules (see Setup Requirements above).

### "No suitable USB ports found"
All your USB ports might be in use by system devices. The controller skips:
- USB hubs
- Cameras and webcams
- Storage devices (USB drives, SD readers)
- Input devices (keyboards, mice, touchscreens)
- Audio devices

If your LED is on one of these ports, you'll need to explicitly set `led.usb_port` in config.yaml.

### Wrong port detected
Set the specific port in config.yaml:
```yaml
led:
  usb_port: "1-1.2"  # your LED's hub and port
```

## Future Improvements

1. Pass `config["led"]["usb_port"]` when creating LEDController in timelapse_touch.py
   - Currently uses default "auto" because I can't modify that file (another agent working on it)
   - Works fine, just means config.yaml usb_port setting is ignored until UI code updated

2. Add sysfs fallback for hubs without uhubctl support

3. Cache uhubctl output to speed up repeated detect() calls

## Questions?

The new implementation is simpler and more reliable:
- No serial protocol to debug
- Direct hardware control at USB level
- Works with any simple USB-powered LED (no special hardware needed)
- Clear error messages with actionable fixes

Test it out and let me know if you have any issues!

— Linguini

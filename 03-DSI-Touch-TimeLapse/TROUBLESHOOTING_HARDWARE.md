# 🛠️ Scenario 03 Hardware Troubleshooting

Use this guide when DSI display, Grove button, or Grove relay behavior is not working as expected.

## 1) DSI display issues

### Symptom: app starts but nothing appears on touchscreen

- Verify Raspberry Pi OS Desktop is active on the DSI screen.
- Launch from SSH and watch logs:
  - `python3 timelapse_touch.py --fullscreen`

### Symptom: touch is rotated or offset

- Adjust display/touch rotation in Raspberry Pi OS settings first.
- Re-test before changing app config.

## 2) Grove Dual Button issues

### Symptom: button press does nothing

Check:

1. Module is connected to socket **D5** on Grove Base Hat.
2. `config.yaml` has:
   - `grove_button.enabled: true`
   - `pin_button1: 5`
   - `pin_button2: 6`
3. Start/stop mapping matches your expectation:
   - `start_stop_button`
   - `stop_button`

## 3) Grove relay issues

### Symptom: relay does not switch

Check:

1. Module is connected to socket **D26** on Grove Base Hat.
2. `config.yaml` has:
   - `grove_relay.enabled: true`
   - `grove_relay.pin: 26`
   - `grove_relay.active_high: true` (or `false` for inverted relay boards)

### Symptom: permission/runtime relay errors

- Ensure dependencies were installed with:
  - `bash install.sh --all`
- Run app with sudo if `/sys/class/gpio` write access is denied.

## 5) Fast fallback strategy

When debugging, disable optional hardware first so capture can still run:

- `grove_button.enabled: false`
- `grove_relay.enabled: false`

Then re-enable one module at a time.

## Related docs

- [HARDWARE_ASSEMBLY.md](HARDWARE_ASSEMBLY.md)
- [GROVE_BASE_HAT_PINOUT.md](GROVE_BASE_HAT_PINOUT.md)
- [USER_MANUAL.md](USER_MANUAL.md)

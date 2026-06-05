# 🛠️ Scenario 03 Hardware Troubleshooting

Use this guide when DSI display, Grove button/light, or USB LED behavior is not working as expected.

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

## 3) Grove WS2813 light issues

### Symptom: LED stays off

Check:

1. Module is connected to socket **PWM** on Grove Base Hat.
2. `config.yaml` has:
   - `grove_light.enabled: true`
   - `pin: 12`
3. `pixel_count` matches your hardware:
   - `20` for Ring
   - `10` for Stick

### Symptom: import/runtime LED errors

- Ensure dependencies were installed with:
  - `bash install.sh --all`
- This installs Python dependencies including `rpi-ws281x` from `requirements.txt`.

## 4) USB LED backend issues

If using USB LED backend instead of Grove:

1. Set `led.backend: usb`.
2. Install tooling if needed (`uhubctl`) via install script with LED options.
3. Re-test capture cycle.

## 5) Fast fallback strategy

When debugging, disable optional hardware first so capture can still run:

- `grove_button.enabled: false`
- `grove_light.enabled: false`

Then re-enable one module at a time.

## Related docs

- [HARDWARE_ASSEMBLY.md](HARDWARE_ASSEMBLY.md)
- [GROVE_BASE_HAT_PINOUT.md](GROVE_BASE_HAT_PINOUT.md)
- [USER_MANUAL.md](USER_MANUAL.md)

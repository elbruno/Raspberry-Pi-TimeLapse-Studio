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

### Symptom: one or both relays do not switch

Check:

1. Relay modules are connected to expected sockets:
   - Relay #1 → **D26**
   - Relay #2 → **D24**
2. `config.yaml` has:
   - `grove_relay.enabled: true`
   - `grove_relay.pin: 26`
   - `grove_relay.active_high: true` (or `false` for inverted relay boards)
   - `grove_relay_2.enabled: true`
   - `grove_relay_2.pin: 24`
   - `grove_relay_2.active_high: true` (or `false` for inverted relay boards)
3. Ensure both relays do **not** share the same BCM pin in config.

### Symptom: permission/runtime relay errors

- Ensure dependencies were installed with:
  - `bash install.sh --all`
- Run app with sudo if `/sys/class/gpio` write access is denied.

## 5) Fast fallback strategy

When debugging, disable optional hardware first so capture can still run:

- `grove_button.enabled: false`
- `grove_relay.enabled: false`
- `grove_relay_2.enabled: false`

Then re-enable one module at a time.

## 6) Camera daemon (RTSP) issues

### Symptom: app stuck on `ON HOLD` when using daemon mode

Check:

1. `config.yaml` camera source mode:
   - `camera.source_mode: daemon_primary` (Option A), or
   - `camera.source_mode: direct_primary` (Option B).
2. Daemon URL is reachable:
   - `camera.daemon.rtsp_url: rtsp://127.0.0.1:8554/unicast`
3. Service status:
   - `sudo systemctl status v4l2rtspserver`
   - or `sudo systemctl status pitimelapse-v4l2rtspserver` (if local fallback unit was created).
4. RTSP port is listening:
   - `ss -ltn | grep 8554`

### Symptom: daemon mode fails, direct mode still works

- Keep using Option B (`direct_primary`) while debugging service startup.
- Verify camera node and ownership:
  - `v4l2-ctl --list-devices`
  - `ls -l /dev/video*`
- If daemon owns `/dev/video0`, direct probing may fail until daemon is stopped.

### Symptom: direct mode fails while daemon is active

- Stop daemon temporarily for diagnostics:
  - `sudo systemctl stop v4l2rtspserver`
  - or `sudo systemctl stop pitimelapse-v4l2rtspserver`
- Test direct camera index in Settings, then restart daemon.

## Related docs

- [HARDWARE_ASSEMBLY.md](HARDWARE_ASSEMBLY.md)
- [GROVE_BASE_HAT_PINOUT.md](GROVE_BASE_HAT_PINOUT.md)
- [USER_MANUAL.md](USER_MANUAL.md)

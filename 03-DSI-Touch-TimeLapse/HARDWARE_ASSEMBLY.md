# 🔌 Scenario 03 Hardware Assembly (DSI + Grove)

This is the canonical physical wiring guide for Scenario 03.

Use it when your question is: **"Where do I plug the shield and sensors?"**

## Required vs optional hardware

### Required (Scenario 03 baseline)

- Raspberry Pi (3B+, 4, or 5)
- DSI touchscreen (for example Freenove 7-inch 800x480)
- USB camera (or your supported camera setup)

### Optional (extra controls/lighting)

- Grove Base Hat for Raspberry Pi (stacked on GPIO header)
- Grove Dual Button
- Grove Relay module #1 (Seeed)
- Grove Relay module #2 (Seeed)

> Scenario 03 works without Grove modules. Grove is optional.

## Physical assembly order

1. Power off the Pi.
2. Connect the DSI ribbon cable to the Pi display connector and your DSI panel.
3. Stack the Grove Base Hat on the Pi GPIO header.
4. Connect optional Grove modules:
   - Dual Button → D5 socket
   - Grove Relay #1 → D26 socket (recommended)
   - Grove Relay #2 → D24 socket (recommended)
5. Connect camera.
6. Power on and boot into Raspberry Pi OS Desktop.

## Exact Grove connections

- **Dual Button**: plug into the socket labeled **D5** (uses BCM 5 and BCM 6)
- **Grove Relay #1**: plug into socket **D26** (uses BCM 26)
- **Grove Relay #2**: plug into socket **D24** (uses BCM 24)

### Quick socket diagram (top view)

Use labels on your actual board if placement differs by revision.

```text
TOP VIEW (Grove Base Hat)

┌─────────────────────────────────────────────┐
│ [ PWM ] [ D5 ] [ D16 ] [ D18 ] [ A0 ] [A2] │
│           ↑                                 │
│        BUTTON                               │
│                                             │
│ [UART] [D22] [D24] [D26] [ A4 ] [A6]       │
│              ↑      ↑                       │
│           RELAY2  RELAY1                    │
│                                             │
│ [I2C] [I2C] [I2C] [ SWD / GPIO ]            │
└─────────────────────────────────────────────┘
```

See full mapping details in [GROVE_BASE_HAT_PINOUT.md](GROVE_BASE_HAT_PINOUT.md).

## Config values that must match wiring

In `config.yaml`:

- `grove_button.pin_button1: 5`
- `grove_button.pin_button2: 6`
- `grove_relay.pin: 26`
- `grove_relay.active_high: true`
- `grove_relay_2.pin: 24`
- `grove_relay_2.active_high: true`

If your board revision differs, trust the socket labels (`D5`, `PWM`) and keep these BCM values aligned.

## Quick sanity checks

- DSI screen shows Raspberry Pi desktop after boot
- App launches on screen with `python3 timelapse_touch.py --fullscreen`
- Button press toggles capture (depending on your button mapping in config)
- Relay #1 and Relay #2 toggle ON before capture and OFF right after capture

## If something does not work

Use [TROUBLESHOOTING_HARDWARE.md](TROUBLESHOOTING_HARDWARE.md).

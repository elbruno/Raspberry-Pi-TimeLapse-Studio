# 🧭 Grove Base Hat Pinout for Scenario 03

This page documents the active pin/socket mapping for Scenario 03 optional Grove hardware.

## Recommended mapping

| Module | Grove socket label | BCM pins used | Config keys |
|---|---|---|---|
| Grove Dual Button | `D5` | BCM 5 + BCM 6 | `grove_button.pin_button1`, `grove_button.pin_button2` |
| Grove WS2813 Ring/Stick | `PWM` | BCM 12 (signal) | `grove_light.pin` |

## Practical plug map

- Plug the **Dual Button** cable into the socket labeled **D5**.
- Plug the **WS2813 LED** cable into the socket labeled **PWM**.

If your hat revision layout looks different, trust the printed socket labels over board position.

## Config examples

### Ring (20 LEDs)

- `grove_light.pixel_count: 20`

### Stick (10 LEDs)

- `grove_light.pixel_count: 10`

## Notes

- Scenario 03 defaults are tuned for Ring (20) in `config.yaml`.
- Software uses BCM numbering, so keep BCM values synchronized with your wiring.
- Grove hardware is optional; Scenario 03 can run without it.

## Legacy reference

Historical expansion notes are preserved in:

- `archive/02-Touch-TimeLapse/GROVE_HARDWARE_PLAN.md`

Use that file for extra context only; Scenario 03 docs are the canonical path.

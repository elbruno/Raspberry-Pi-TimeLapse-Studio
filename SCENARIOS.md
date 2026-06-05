# 🎯 Scenario Chooser

Use this page to quickly pick the right PiTimeLapse setup.

## Quick comparison

| Scenario | Interface | Platform | Best for | Setup time |
|---|---|---|---|---|
| [**Scenario 01 — WebApp**](01-WebApp-TimeLapse/README.md) | Web browser (Flask) | Windows, macOS, Linux, Raspberry Pi | Remote monitoring from phone/laptop | ~5–10 min |
| [**Scenario 03 — DSI Touch**](03-DSI-Touch-TimeLapse/README.md) | Native touchscreen (Pygame) | Raspberry Pi + DSI display | Standalone kiosk capture station | ~30–45 min |

> ⚠️ [Scenario 02](archive/02-Touch-TimeLapse/README.md) is archived (legacy SPI touch flow).

## Decision tree

- If you want control from another device on your network, use **Scenario 01**.
- If you want an on-device touchscreen kiosk on Raspberry Pi, use **Scenario 03**.
- If you are unsure, start with **Scenario 01** first, then move to Scenario 03.

## Where to start next

- New to the repo: [GETTING_STARTED.md](GETTING_STARTED.md)
- Need Scenario 03 hardware wiring: [03-DSI-Touch-TimeLapse/HARDWARE_ASSEMBLY.md](03-DSI-Touch-TimeLapse/HARDWARE_ASSEMBLY.md)
- Need Raspberry Pi cleanup/profile guidance: [99-InitRPi/rpi-cleanup-ssh-commands.md](99-InitRPi/rpi-cleanup-ssh-commands.md)
- Need archive policy and migration context: [DEPRECATIONS.md](DEPRECATIONS.md)

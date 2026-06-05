# 🗂️ Deprecations and Legacy Paths

## Scenario 02 — Touch TimeLapse (SPI) status

Scenario 02 is **archived** and kept for historical/legacy reference.

- Archive location: [archive/02-Touch-TimeLapse/README.md](archive/02-Touch-TimeLapse/README.md)
- Active touchscreen scenario: [03-DSI-Touch-TimeLapse/README.md](03-DSI-Touch-TimeLapse/README.md)

## Why Scenario 03 is the active path

Scenario 03 is documented as the current touchscreen route because it targets DSI displays and avoids the old SPI LCD driver setup flow.

## Migration guidance

If you were following Scenario 02 docs:

1. Move to [SCENARIOS.md](SCENARIOS.md) and select Scenario 03.
2. Follow [03-DSI-Touch-TimeLapse/USER_MANUAL.md](03-DSI-Touch-TimeLapse/USER_MANUAL.md).
3. Use [99-InitRPi/rpi-cleanup-ssh-commands.md](99-InitRPi/rpi-cleanup-ssh-commands.md) with the `touch` profile.

## Notes

- Legacy docs remain in `archive/` for reference only.
- Active onboarding and setup documentation should point to Scenario 01 or Scenario 03.

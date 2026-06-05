# 🧭 Cleanup Profiles

Choose the cleanup profile before installing app dependencies.

## `web` profile

Use for [Scenario 01](../01-WebApp-TimeLapse/README.md):

- Browser-based control
- Can run headless
- Removes more desktop components

## `touch` profile

Use for [Scenario 03](../03-DSI-Touch-TimeLapse/README.md):

- DSI touchscreen kiosk workflow
- Keeps desktop/X11 components needed by touchscreen UI
- Correct profile for DSI display setups

## Rule of thumb

- If your UI is in a browser: `web`
- If your UI is on the Pi touchscreen: `touch`

## Commands

Dry run:

- `bash rpi-timelapse-cleanup.sh --profile web`
- `bash rpi-timelapse-cleanup.sh --profile touch`

Apply:

- `sudo bash rpi-timelapse-cleanup.sh --profile web --apply --yes`
- `sudo bash rpi-timelapse-cleanup.sh --profile touch --apply --yes`

## Scenario 03 caution

For DSI touch setups, do not run SPI LCD setup scripts (`LCD-show`, `LCD35-show`, `MHS35-show`, or `--setup-lcd` from legacy flow).

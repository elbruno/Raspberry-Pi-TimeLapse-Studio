# 🚀 Getting Started

This guide is the fastest path from clone to a working setup.

## Step 1: pick your scenario

Use [SCENARIOS.md](SCENARIOS.md) if you are not sure.

## Step 2: follow the right path

### Path A — Scenario 01 (web app, recommended first)

1. Open [01-WebApp-TimeLapse/README.md](01-WebApp-TimeLapse/README.md)
2. Install requirements
3. Run `python main.py validate`
4. Run `python main.py`

Best for: cross-platform use, remote browser access, quick validation.

### Path B — Scenario 03 (DSI touchscreen kiosk)

1. Open [03-DSI-Touch-TimeLapse/README.md](03-DSI-Touch-TimeLapse/README.md)
2. If fresh SD card, run touch cleanup profile first using [99-InitRPi/rpi-cleanup-ssh-commands.md](99-InitRPi/rpi-cleanup-ssh-commands.md)
3. Install with `install.sh --all`
4. Reboot and test launch from SSH first

Hardware wiring quick links for Scenario 03:

- [HARDWARE_ASSEMBLY.md](03-DSI-Touch-TimeLapse/HARDWARE_ASSEMBLY.md)
- [GROVE_BASE_HAT_PINOUT.md](03-DSI-Touch-TimeLapse/GROVE_BASE_HAT_PINOUT.md)
- [TROUBLESHOOTING_HARDWARE.md](03-DSI-Touch-TimeLapse/TROUBLESHOOTING_HARDWARE.md)

Best for: dedicated Raspberry Pi touch station.

## Step 3: avoid the old path

- Scenario 02 in the root folder is not the active touchscreen scenario.
- Use Scenario 03 for all current touchscreen setups.
- See [DEPRECATIONS.md](DEPRECATIONS.md) for details.

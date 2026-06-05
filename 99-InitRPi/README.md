# 🧹 Raspberry Pi Initialization & Cleanup

This folder contains the disk cleanup and first-use provisioning tools used before installing scenarios.

## Which cleanup profile should I use?

- Use `web` profile for [Scenario 01](../01-WebApp-TimeLapse/README.md) headless/web setups.
- Use `touch` profile for [Scenario 03](../03-DSI-Touch-TimeLapse/README.md) touchscreen setups.

## Start here

- Detailed command flow: [rpi-cleanup-ssh-commands.md](rpi-cleanup-ssh-commands.md)
- Profile guidance: [CLEANUP_PROFILES.md](CLEANUP_PROFILES.md)
- Script: [rpi-timelapse-cleanup.sh](rpi-timelapse-cleanup.sh)

## Important for Scenario 03 (DSI)

- Keep desktop/X11 stack (use `touch` profile)
- Do not install SPI LCD driver scripts
- Follow Scenario 03 docs after cleanup

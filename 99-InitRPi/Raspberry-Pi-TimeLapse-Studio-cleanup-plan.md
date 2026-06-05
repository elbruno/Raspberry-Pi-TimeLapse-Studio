# Raspberry Pi TimeLapse Studio cleanup plan

This plan is designed for the repository:

<https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio>

## Goal

Free disk space on a dedicated Raspberry Pi while preserving everything needed to run one of these scenarios:

- `01-WebApp-TimeLapse` — Flask + OpenCV + Pillow + optional `python3-picamera2`
- `02-Touch-TimeLapse` — **legacy/archived** SPI-touch scenario (reference only)
- `03-DSI-Touch-TimeLapse` — same app engine as Scenario 02, but for driver-free DSI touchscreens

## What the repo actually needs

From the current repo:

- Web scenario Python deps: Flask, PyYAML, python-dotenv, opencv-python-headless, Pillow
- Touch scenario Python deps: pygame, psutil, opencv-python-headless, numpy, pyyaml
- Pi Camera path: `python3-picamera2` is intentionally installed with `apt`, not `pip`

## Strategy

1. Inspect current disk usage and large directories.
2. Snapshot large optional desktop packages that are safe to remove on a dedicated timelapse Pi.
3. Use one of two cleanup profiles:
   - `web`: keep a headless/SSH/VS Code friendly device and remove the desktop stack.
   - `touch`: keep the desktop/X11 stack for the touchscreen app and only remove non-essential apps.
4. Purge packages conservatively.
5. Run `autoremove`, `autoclean`, `clean`, trim journals, and delete stale VS Code server installs.
6. Reinstall only the repo dependencies and validate the setup.
7. Optionally enable internal-device elevated defaults so interactive sessions
   auto-escalate to root and routine commands no longer need manual `sudo`.

## Why two profiles matter

- The touchscreen scenario relies on a desktop/X11 environment for its LCD rendering workflow.
- The web scenario does not need the desktop stack and can save much more space by removing it.
- Scenario 03 also uses the `touch` profile because it needs the same desktop/X11 stack, even though its DSI panel does **not** need a separate LCD driver installation step.

## Safe first run

Always start with a dry run:

```bash
bash rpi-timelapse-cleanup.sh --profile web
```

or

```bash
bash rpi-timelapse-cleanup.sh --profile touch
```

## Apply changes

When the dry run looks correct:

```bash
sudo bash rpi-timelapse-cleanup.sh --profile web --apply
```

or

```bash
sudo bash rpi-timelapse-cleanup.sh --profile touch --apply
```

For trusted/internal devices, you can fold in auto-root defaults during the
same first-use flow:

```bash
sudo bash rpi-timelapse-cleanup.sh --profile touch --apply --yes --enable-elevated-defaults --elevated-user pi
```

## Recommendation

Use `web` if this Pi is mainly going to run the browser-based timelapse app and you manage it over SSH/VS Code.
Use `touch` if this Pi must keep the local LCD/touchscreen UI for **Scenario 03** (and only for legacy Scenario 02 if explicitly needed).

## Scenario 03 note

Scenario 03 is intentionally different from Scenario 02 during hardware bring-up:

- keep the desktop/X11 stack
- use the `touch` cleanup profile
- install app dependencies normally
- **do not** install SPI/GPIO LCD drivers
- assume the DSI display is **plug and play** unless Raspberry Pi OS proves otherwise

# 👆 Scenario 03 — DSI Touch TimeLapse

A Raspberry Pi **DSI touchscreen** scenario using the exact same app engine as [Scenario 02](../02-Touch-TimeLapse/), pre-wired for displays like:

- **Freenove 7 Inch Touchscreen Monitor** (ASIN `B0B44VZTRG`)
- 800×480, capacitive touch, DSI ribbon connection

---

## What is different vs Scenario 02?

- ✅ Same UI, same capture engine, same features
- ✅ Same camera, USB storage, LED relay, Grove button/light support
- ✅ Same code quality and behavior
- 🔁 Different scenario folder + config so you can tune it independently
- 🧩 Install flow adapted for **DSI** displays (no SPI LCD driver step)

This scenario launches the Scenario 02 app internally, while keeping local files for:

- `config.yaml` (your DSI profile settings)
- desktop shortcut and autostart
- DSI-focused installation notes

---

## Fresh SD card setup (recommended)

If you're starting from a **brand-new SD card**, use this order:

1. Flash **Raspberry Pi OS Desktop**
2. Boot once and verify the **DSI screen already works**
3. Run the **touch cleanup profile** to reclaim space
4. Install Scenario 03
5. Reboot and test from SSH first

For trusted/internal devices, step 3 can also enable the new
**elevated defaults** mode so future SSH sessions start in a root shell and the
desktop launcher can use passwordless elevation automatically.

📖 Full walkthrough → [**USER_MANUAL.md**](USER_MANUAL.md)

> ✅ For this scenario, **do not install any LCD driver package or SPI LCD script**.
> The Freenove DSI panel should be treated as **plug and play** on Raspberry Pi OS Desktop.

---

## Quick start (Raspberry Pi + DSI display)

1. Clone the repo and open this folder:

```bash
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
```

1. Clean disk space (optional but highly recommended):

```bash
# Dry run first (shows what would be removed)
bash cleanup.sh

# Apply cleanup
bash cleanup.sh --apply --yes

# Optional for trusted/internal devices:
# enable passwordless sudo + auto-root shells during first-use cleanup
sudo bash ../99-InitRPi/rpi-timelapse-cleanup.sh --profile touch --apply --yes --enable-elevated-defaults --elevated-user pi
```

1. Install the requirements for Scenario 03:

```bash
bash install.sh --all
```

1. Reboot and launch:

```bash
sudo reboot
# or run manually after reboot
python3 timelapse_touch.py --fullscreen
```

The desktop shortcut now uses a smart launcher: it runs directly when already
root, uses passwordless `sudo` when configured, and otherwise falls back to a
normal user launch with a warning that Grove WS281x LED access may be limited.

---

## Notes for your Freenove DSI display

- The panel is **DSI**, not HDMI, and not a GPIO/SPI TFT.
- On Raspberry Pi OS Desktop, it is generally driver-free.
- Use the normal Raspberry Pi desktop stack — no special LCD overlay install is expected here.
- If touch appears offset or rotation is wrong, check display/touch rotation settings in Raspberry Pi OS.
- If rendering from SSH, keep a desktop session active on the Pi (`DISPLAY=:0`) so the GUI can appear on the touchscreen.
- Do **not** run `LCD-show`, `LCD35-show`, `MHS35-show`, or `02-Touch-TimeLapse/install.sh --setup-lcd` for this display.

---

## Configuration

Edit `config.yaml` in this folder.

A practical first tweak for many single-camera Pi setups:

- `camera.index: 0`

Scenario 03 now defaults to an `800x450` app window so it fits nicely on
common `800x480` DSI touchscreens.

---

## Project layout

```text
03-DSI-Touch-TimeLapse/
├── cleanup.sh          # Scenario 03 cleanup helper (keeps desktop/X11)
├── timelapse_touch.py   # Launcher that reuses Scenario 02 app code
├── config.yaml          # Scenario 03 local config
├── install.sh           # DSI-focused installer
├── install-shortcut.sh  # Desktop shortcut + optional autostart
└── requirements.txt     # Reuses Scenario 02 Python dependencies
```

---

## Need full feature docs?

Use Scenario 03 + Scenario 02 documentation together:

- [Scenario 03 User Manual](USER_MANUAL.md)
- [Scenario 02 README](../02-Touch-TimeLapse/README.md)
- [Scenario 02 User Manual](../02-Touch-TimeLapse/USER_MANUAL.md)
- [Cleanup SSH guide](../99-InitRPi/rpi-cleanup-ssh-commands.md)
- [Internal-device elevation helper](../99-InitRPi/enable-device-elevation.sh)

# 👆 Scenario 03 — DSI Touch TimeLapse

A Raspberry Pi **DSI touchscreen** scenario that reuses the shared touchscreen app engine, pre-wired for displays like:

- **Freenove 7 Inch Touchscreen Monitor** (ASIN `B0B44VZTRG`)
- 800×480, capacitive touch, DSI ribbon connection

> ⚠️ **Scenario 02 in the root folder is archived.** If you need historical SPI-touch references, use [archive/02-Touch-TimeLapse](../archive/02-Touch-TimeLapse/README.md). For current touchscreen setup, stay in Scenario 03 docs.

---

## What is different in Scenario 03?

- ✅ Same UI, same capture engine, same features
- ✅ Same camera, USB storage, LED relay, Grove button/light support
- ✅ Same code quality and behavior
- 🔁 Different scenario folder + config so you can tune it independently
- 🧩 Install flow adapted for **DSI** displays (no SPI LCD driver step)

This scenario reuses the shared touchscreen engine while keeping local files for:

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

`--all` now installs dependencies plus the desktop shortcut, but **does not**
enable launch-on-boot. Use `bash install.sh --autostart` only if you explicitly
want the app to start automatically when the device boots.

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

## Optional hardware wiring (Grove)

Scenario 03 supports optional Grove hardware for physical controls/status:

- Grove Dual Button
- Grove WS2813 Ring/Stick status light

Use these docs for exact connections:

- [Hardware assembly (where to plug each module)](HARDWARE_ASSEMBLY.md)
- [Grove Base Hat pin/socket mapping](GROVE_BASE_HAT_PINOUT.md)
- [Hardware troubleshooting](TROUBLESHOOTING_HARDWARE.md)

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
├── timelapse_touch.py   # Launcher for the shared touchscreen app engine
├── config.yaml          # Scenario 03 local config
├── install.sh           # DSI-focused installer
├── install-shortcut.sh  # Desktop shortcut + optional opt-in autostart
└── requirements.txt     # Shared touchscreen Python dependencies
```

---

## Need full feature docs?

Start with Scenario 03 documentation. Use archived Scenario 02 docs only as legacy reference:

- [Scenario 03 User Manual](USER_MANUAL.md)
- [Scenario chooser](../SCENARIOS.md)
- [Hardware assembly guide](HARDWARE_ASSEMBLY.md)
- [Grove pinout mapping](GROVE_BASE_HAT_PINOUT.md)
- [Hardware troubleshooting](TROUBLESHOOTING_HARDWARE.md)
- [Legacy Scenario 02 README (archive)](../archive/02-Touch-TimeLapse/README.md)
- [Legacy Scenario 02 User Manual (archive)](../archive/02-Touch-TimeLapse/USER_MANUAL.md)
- [Cleanup SSH guide](../99-InitRPi/rpi-cleanup-ssh-commands.md)
- [Internal-device elevation helper](../99-InitRPi/enable-device-elevation.sh)

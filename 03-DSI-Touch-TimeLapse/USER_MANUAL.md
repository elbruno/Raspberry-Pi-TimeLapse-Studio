# 📖 Scenario 03 — DSI Touch TimeLapse User Manual

A complete setup guide for running **PiTimeLapse DSI Touch** on a Raspberry Pi with a **driver-free DSI touchscreen**, such as the **Freenove 7-inch 800×480 capacitive display**.

> 📖 Part of [PiTimeLapse Lab](../README.md) · Quick overview → [README.md](README.md)
> 💡 Scenario 03 reuses the shared touchscreen app engine, but the hardware setup is different: **no SPI LCD driver install step is required**.

---

## What makes Scenario 03 different?

Scenario 03 includes the same touchscreen feature set:

- touchscreen UI
- camera preview
- time-lapse capture
- USB storage fallback
- optional dual-relay support
- optional Grove button support

But it is tuned for **DSI touchscreens** that already work with Raspberry Pi OS Desktop.

> ⚠️ The active touchscreen path is Scenario 03. Scenario 02 is archived and should be treated as legacy reference only.

Need physical connection guidance for Grove modules? Start here:

- [HARDWARE_ASSEMBLY.md](HARDWARE_ASSEMBLY.md)
- [GROVE_BASE_HAT_PINOUT.md](GROVE_BASE_HAT_PINOUT.md)
- [TROUBLESHOOTING_HARDWARE.md](TROUBLESHOOTING_HARDWARE.md)

That means:

- ✅ keep the Raspberry Pi desktop/X11 environment
- ✅ use the normal `touch` cleanup profile when reclaiming space
- ✅ install app dependencies only
- ❌ **do not install any LCD driver package or SPI display overlay**
- ❌ **do not run `LCD-show`, `LCD35-show`, `MHS35-show`, or similar scripts**

---

## 1. Start from a brand-new SD card

### Recommended OS image

Use **Raspberry Pi OS Desktop**.

Do **not** use Lite for this scenario because the touchscreen app expects a graphical desktop session.

### In Raspberry Pi Imager, set these advanced options

Before flashing the card, open the advanced options and configure:

- **hostname** (for example: `pitimelapse-dsi`)
- **enable SSH**
- **Wi-Fi** (if needed)
- **username/password**
- **locale / keyboard / timezone**

This saves time later and makes SSH setup much easier.

---

## 2. First boot checks

Boot the Pi with the DSI display connected.

You should expect:

- the Raspberry Pi desktop appears on the screen
- touch input works without a custom driver install
- the Pi is reachable over SSH

If the display lights up and the desktop appears, that is the big green flag. Tiny victory dance permitted.

### Connect over SSH

```bash
ssh pi@<your-pi-ip>
```

Optional sanity checks:

```bash
echo $XDG_SESSION_TYPE
ls /tmp/.X11-unix
```

---

## 3. Clean the fresh SD card first

A fresh Raspberry Pi OS Desktop install still carries extra packages and caches. For Scenario 03, use the existing cleanup flow with the **touch** profile.

From the Scenario 03 folder, you can use the local helper script:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
bash cleanup.sh            # dry run
bash cleanup.sh --apply --yes
```

This helper forwards to the shared cleanup engine with the correct `touch` profile.

### Dry run first

```bash
cd ~
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/99-InitRPi
bash rpi-timelapse-cleanup.sh --profile touch
```

### Apply cleanup

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
sudo bash rpi-timelapse-cleanup.sh --profile touch --apply --yes
sudo apt update
```

### Optional — internal-device elevated defaults

If this Pi is a trusted internal device and you want interactive logins to land
in a root shell automatically, fold that into the same first-use step:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
sudo bash rpi-timelapse-cleanup.sh --profile touch --apply --yes --enable-elevated-defaults --elevated-user pi
sudo apt update
```

This enables:

- passwordless `sudo` for the selected user
- automatic root shells on interactive login/SSH
- access to the original user's `~/.local` Python packages while running as root

Use this mode only on dedicated/internal devices.

Why `touch` profile?

- it keeps the desktop/X11 stack required by the touchscreen app
- it removes non-essential bloat
- it is the right profile for Scenario 03 (and legacy Scenario 02 only when explicitly needed)

---

## 4. Install Scenario 03

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
bash install.sh --all
```

What `--all` does here:

- installs SDL2 and Python dependencies
- includes relay tooling support
- creates the desktop shortcut
- **does not install any LCD driver**

Autostart is now **disabled by default**. If you want the app to launch on
boot, enable it explicitly later with:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
bash install.sh --autostart
```

### Important

For this scenario, the display is treated as **plug and play**.

Do not run:

- `bash install.sh --setup-lcd` from Scenario 02
- `LCD-show`
- `LCD35-show`
- `MHS35-show`
- any SPI TFT display setup script

Those are for small SPI/GPIO displays, not for your Freenove DSI panel.

---

## 5. Reboot and test

```bash
sudo reboot
```

After reboot, test from SSH first:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
python3 timelapse_touch.py --fullscreen
```

If you enabled internal-device elevated defaults during cleanup, reconnecting by
SSH should already place you in a root shell, so later maintenance commands no
longer need manual `sudo`.

This is the best first test because:

- the app renders on the touchscreen
- logs remain visible in your SSH session
- you can stop it with `Ctrl+C`

Once that works, you can use the desktop shortcut or autostart normally.

---

## 6. Daily use

### Manual launch

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
python3 timelapse_touch.py --fullscreen
```

### Desktop shortcut

The installer creates a desktop icon named:

- **PiTimeLapse DSI Touch**

The shortcut uses a smart launcher that:

- runs the app directly when the session is already root
- uses passwordless `sudo` automatically when available
- falls back to a normal user launch with a warning if elevation is unavailable

### Autostart

Autostart is **not** enabled by default.

Enable it only when you want boot-time launch:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
bash install.sh --autostart
```

---

## 7. Configuration

Edit:

- `03-DSI-Touch-TimeLapse/config.yaml`

Suggested first settings:

```yaml
camera:
  index: 0
capture:
  interval_seconds: 30
```

If the wrong camera opens, try `1` instead of `0`.

---

## 8. Troubleshooting

### The display works, but the app does not show up

Make sure the Raspberry Pi desktop session is running. Scenario 03 renders via the desktop/X11 path.

Test from SSH:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
python3 timelapse_touch.py --fullscreen
```

### Touch works but is rotated or offset

This is usually an OS display/touch mapping issue, not an app issue.

Check Raspberry Pi OS display rotation/touch settings before changing the app.

### I accidentally ran an SPI LCD setup script

If you installed an SPI/TFT driver meant for a different screen, revert that change before debugging Scenario 03 further. The DSI display should be used with the stock desktop setup.

### Camera not detected

Edit `config.yaml` and try a different `camera.index`.

---

## 9. Related docs

- [Scenario 03 README](README.md)
- [Scenario chooser](../SCENARIOS.md)
- [Hardware assembly guide](HARDWARE_ASSEMBLY.md)
- [Grove pinout mapping](GROVE_BASE_HAT_PINOUT.md)
- [Hardware troubleshooting](TROUBLESHOOTING_HARDWARE.md)
- [Legacy Scenario 02 README (archive)](../archive/02-Touch-TimeLapse/README.md)
- [Legacy Scenario 02 User Manual (archive)](../archive/02-Touch-TimeLapse/USER_MANUAL.md)
- [Raspberry Pi cleanup commands](../99-InitRPi/rpi-cleanup-ssh-commands.md)

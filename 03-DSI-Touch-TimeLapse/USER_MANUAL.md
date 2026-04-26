# 📖 Scenario 03 — DSI Touch TimeLapse User Manual

A complete setup guide for running **PiTimeLapse DSI Touch** on a Raspberry Pi with a **driver-free DSI touchscreen**, such as the **Freenove 7-inch 800×480 capacitive display**.

> 📖 Part of [PiTimeLapse Lab](../README.md) · Quick overview → [README.md](README.md)
> 💡 Scenario 03 reuses the full Scenario 02 app engine, but the hardware setup is different: **no SPI LCD driver install step is required**.

---

## What makes Scenario 03 different?

Scenario 03 uses the same application features as [Scenario 02](../02-Touch-TimeLapse/README.md):

- touchscreen UI
- camera preview
- time-lapse capture
- USB storage fallback
- optional LED relay support
- optional Grove button / Grove status light support

But it is tuned for **DSI touchscreens** that already work with Raspberry Pi OS Desktop.

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

Why `touch` profile?

- it keeps the desktop/X11 stack required by the touchscreen app
- it removes non-essential bloat
- it is the right profile for both Scenario 02 and Scenario 03

---

## 4. Install Scenario 03

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
bash install.sh --all
```

What `--all` does here:

- installs SDL2 and Python dependencies
- optionally includes LED tooling support
- creates desktop shortcut + autostart
- **does not install any LCD driver**

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

### Autostart

If you used `bash install.sh --all`, autostart is already configured.

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
- [Scenario 02 README](../02-Touch-TimeLapse/README.md)
- [Scenario 02 User Manual](../02-Touch-TimeLapse/USER_MANUAL.md)
- [Raspberry Pi cleanup commands](../99-InitRPi/rpi-cleanup-ssh-commands.md)

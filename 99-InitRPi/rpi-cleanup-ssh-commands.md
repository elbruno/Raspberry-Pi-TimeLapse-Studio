# Raspberry Pi Cleanup — SSH Quick Commands

Copy-paste these commands when connected to your Pi via SSH.

> 📌 **Doc split:** [`../02-Touch-TimeLapse/README.md`](../02-Touch-TimeLapse/README.md) is the **quick guide** for the touchscreen scenario. This file is the **detailed bring-up guide** when you want the full provisioning flow and explanations.
> **Context**: A fresh Raspberry Pi OS install + updates typically uses ~5.3 GB on an 8 GB card,
> leaving only ~1.2 GB free. This script recovers space by removing desktop bloat, unused locales,
> docs, old logs, and apt caches.

## Prerequisites

```bash
# Connect to your Pi (replace with your Pi's hostname or IP)
ssh pi@raspberrypi.local
```

## 1. Check current disk usage

```bash
df -h /
```

## 2. Clone or update the repo

```bash
cd ~
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio
```

## 3. Dry run — inspect what would be removed

Pick the profile that matches your scenario:

### Web profile (headless / SSH / VS Code)

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
bash rpi-timelapse-cleanup.sh --profile web
```

### Touch profile (LCD touchscreen UI)

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
bash rpi-timelapse-cleanup.sh --profile touch
```

Review the output. Nothing is modified during a dry run.  
Check the **[7/7] Reclaimable filesystem areas** section — it shows how much space locales, docs, man pages, and apt lists use.

If you do not need the detailed cleanup flow, you can skip back to [`../02-Touch-TimeLapse/README.md`](../02-Touch-TimeLapse/README.md) and use the short install path there.

## 4. Apply the cleanup

> **Warning**: The cleanup removes VS Code server caches. If you are connected via VS Code
> Remote SSH, your session will disconnect. Reconnecting after the script finishes will
> re-download it automatically. Use a plain SSH terminal for this step.

### Web profile

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
sudo bash rpi-timelapse-cleanup.sh --profile web --apply
```

### Touch profile

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
sudo bash rpi-timelapse-cleanup.sh --profile touch --apply
```

Add `--yes` to skip the confirmation prompt:

```bash
sudo bash rpi-timelapse-cleanup.sh --profile web --apply --yes
```

## 5. Refresh apt lists (required after cleanup)

The script clears `/var/lib/apt/lists/` to save space. Refresh before installing anything:

```bash
sudo apt update
```

## 6. Reinstall project dependencies

### For `01-WebApp-TimeLapse`

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/01-WebApp-TimeLapse
pip3 install -r requirements.txt --break-system-packages
python3 main.py validate
```

### For `02-Touch-TimeLapse`

#### Step 1 — LCD driver (first time / after cleanup)

If you have a 3.5" SPI LCD (Kuman SC06 or compatible), install the LCD driver first.
This switches the Pi to X11 mode, configures SPI, and reboots:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
bash install.sh --setup-lcd   # installs goodtft driver → reboots the Pi
```

> ⚠️ The Pi will reboot automatically. Reconnect via SSH after reboot.

#### Step 2 — Software dependencies (after reboot)

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
bash install.sh --all        # full install: SDL2 + pip + LED + desktop shortcut
sudo reboot               # recommended: ensures display drivers + autostart work
# Other options:
# bash install.sh              # base install only (SDL2 + pip packages)
# bash install.sh --with-led   # base + uhubctl for USB LED control
# bash install.sh --autostart  # base + desktop shortcut + autostart on boot
```

> 💡 The autostart setup in `02-Touch-TimeLapse/install-shortcut.sh` now also creates a **user-level override** for `polkit-mate-authentication-agent-1` when present. This prevents the duplicate PolicyKit popup sometimes seen on mixed LXDE/MATE desktop installs.

### For `03-DSI-Touch-TimeLapse`

Scenario 03 uses the same **touch** cleanup profile because it still needs the desktop/X11 stack.

The difference is important:

- **keep** Raspberry Pi OS Desktop
- **do not** install any SPI/GPIO LCD driver
- **do not** run `LCD-show` or `install.sh --setup-lcd`
- the DSI display is expected to be **plug and play**

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
bash install.sh --all
sudo reboot
```

After reboot, test from SSH first:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
python3 timelapse_touch.py --fullscreen
```

## 7. Start the application

### Web app

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/01-WebApp-TimeLapse
python3 main.py
```

Open `http://<pi-hostname>:5000` in your browser.

### Touch app

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
python3 timelapse_touch.py --fullscreen
```

### DSI touch app

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
python3 timelapse_touch.py --fullscreen
```

## 8. Verify disk savings

```bash
df -h /
```

---

## Quick reference — all-in-one (web profile)

```bash
# SSH in and run everything in one go
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
sudo bash rpi-timelapse-cleanup.sh --profile web --apply --yes
sudo apt update
cd ~/Raspberry-Pi-TimeLapse-Studio/01-WebApp-TimeLapse
pip3 install -r requirements.txt --break-system-packages
python3 main.py validate
```

## Quick reference — all-in-one (touch profile)

```bash
# SSH in and run everything in one go
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
sudo bash rpi-timelapse-cleanup.sh --profile touch --apply --yes

# Step 1: LCD driver — reboots the Pi automatically
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
bash install.sh --setup-lcd
# ⚠ Pi reboots here — reconnect via SSH, then continue:

# Step 2: Software dependencies (run after reboot)
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
bash install.sh --all
sudo reboot
```

## Quick reference — all-in-one (Scenario 03 DSI touch)

```bash
# SSH in and run everything in one go
cd ~
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd ~/Raspberry-Pi-TimeLapse-Studio/99-InitRPi
sudo bash rpi-timelapse-cleanup.sh --profile touch --apply --yes
sudo apt update

# DSI display: no LCD driver install step
cd ~/Raspberry-Pi-TimeLapse-Studio/03-DSI-Touch-TimeLapse
bash install.sh --all
sudo reboot
```

## What gets cleaned

| Area | Estimated savings | Details |
| ---- | ----------------- | ------- |
| Desktop packages | 200-800 MB | LibreOffice, Wolfram, Chromium, Thonny, VLC, etc. |
| Unused locales | 100-200 MB | Keeps only `en`, `en_US`, `en_GB` |
| Package docs | 50-150 MB | Keeps copyright files for license compliance |
| Apt cache + lists | 50-150 MB | Re-fetched with `sudo apt update` |
| Journal + old logs | 20-50 MB | Vacuums to 7 days, removes rotated logs |
| VS Code server | 100-300 MB | Re-downloaded on next Remote SSH connect |
| Python `__pycache__` | 5-20 MB | Rebuilt automatically |
| Pip/thumbnail cache | 5-50 MB | Rebuilt as needed |

# Raspberry Pi Cleanup — SSH Quick Commands

Copy-paste these commands when connected to your Pi via SSH.

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

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
chmod +x install.sh
./install.sh --all        # full install: SDL2 + pip + LED + desktop shortcut
# Other options:
# ./install.sh              # base install only (SDL2 + pip packages)
# ./install.sh --with-led   # base + uhubctl for USB LED control
# ./install.sh --autostart  # base + desktop shortcut + autostart on boot
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
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
chmod +x install.sh
./install.sh --all
```

## What gets cleaned

| Area | Estimated savings | Details |
|------|------------------|---------|
| Desktop packages | 200-800 MB | LibreOffice, Wolfram, Chromium, Thonny, VLC, etc. |
| Unused locales | 100-200 MB | Keeps only `en`, `en_US`, `en_GB` |
| Package docs | 50-150 MB | Keeps copyright files for license compliance |
| Apt cache + lists | 50-150 MB | Re-fetched with `sudo apt update` |
| Journal + old logs | 20-50 MB | Vacuums to 7 days, removes rotated logs |
| VS Code server | 100-300 MB | Re-downloaded on next Remote SSH connect |
| Python `__pycache__` | 5-20 MB | Rebuilt automatically |
| Pip/thumbnail cache | 5-50 MB | Rebuilt as needed |

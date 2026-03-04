# 📖 Touch TimeLapse — User Manual

A complete guide to setting up, configuring, and using the **PiTimeLapse Touch** application on your Raspberry Pi with a 3.5" touchscreen display.

> 📖 Part of [PiTimeLapse Lab](../README.md) · Developer reference → [README.md](README.md) · Labs → [labs/](../labs/README.md)

---

## Table of Contents

1. [What Is Touch TimeLapse?](#1-what-is-touch-timelapse)
2. [What You Need](#2-what-you-need)
3. [Setting Up Your Raspberry Pi](#3-setting-up-your-raspberry-pi)
4. [Installing the LCD Display](#4-installing-the-lcd-display)
5. [Installing the Application](#5-installing-the-application)
6. [Launching the App](#6-launching-the-app)
7. [Using the Main Screen](#7-using-the-main-screen)
8. [Using the Settings Screen](#8-using-the-settings-screen)
9. [USB Storage](#9-usb-storage)
10. [USB LED Flash Light](#10-usb-led-flash-light)
11. [Desktop Shortcut & Autostart](#11-desktop-shortcut--autostart)
12. [Configuration File Reference](#12-configuration-file-reference)
13. [Troubleshooting](#13-troubleshooting)
14. [FAQ](#14-faq)

---

## 1. What Is Touch TimeLapse?

Touch TimeLapse is a **standalone time-lapse photo capture station** that runs on a Raspberry Pi with a small touchscreen. Once set up, you don't need a keyboard, mouse, or network connection — just tap the screen to start capturing.

**Key capabilities:**

- 📸 Captures photos at a configurable interval (every 1 second to 1 hour)
- 👆 Full touchscreen control — no keyboard needed
- 💾 Auto-saves to USB drive (or local storage if no USB is connected)
- 📷 Live camera preview between captures
- ⏱️ Countdown timer showing seconds until the next photo
- 📊 Storage monitor showing free space and estimated remaining photos
- 💡 Optional USB LED flash to illuminate the scene before each capture
- ⚙️ In-app settings — adjust everything from the touchscreen

---

## 2. What You Need

### Required

| Item | Notes |
|------|-------|
| **Raspberry Pi** | Model 3B+, 4, or 5 |
| **3.5" TFT touchscreen** | Waveshare, Kuman SC06, or compatible (480×320, SPI) |
| **USB webcam** | Any USB camera supported by Linux |
| **MicroSD card** | 16 GB or larger with Raspberry Pi OS (Desktop version) |
| **Power supply** | Official Pi power supply recommended |

### Optional

| Item | Notes |
|------|-------|
| **USB flash drive** | For saving photos to removable storage |
| **USB LED light** | Any USB-powered LED light (ring light, strip, desk lamp) — controlled via USB port power |
| **Pi Camera Module** | Alternative to USB webcam (picamera2 support planned) |

### For Initial Setup

| Item | Notes |
|------|-------|
| **Another computer** | To SSH into the Pi during setup |
| **Network connection** | WiFi or Ethernet for cloning the repo and installing packages |

---

## 3. Setting Up Your Raspberry Pi

### 3.1 Install Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Flash **Raspberry Pi OS (Desktop)** to your MicroSD card
   > ⚠️ You must use the **Desktop** version — the Lite version has no graphical environment and the app won't render on the LCD.
3. During flashing, set up WiFi credentials and enable SSH in the advanced settings
4. Insert the card and boot the Pi

### 3.2 Find Your Pi on the Network

From your computer, find the Pi's IP address:

```bash
# Option A — if your network supports .local names
ping raspberrypi.local

# Option B — scan your network
nmap -sn 192.168.1.0/24
```

### 3.3 Connect via SSH

```bash
ssh pi@<your-pi-ip>
# Default password: raspberry (change it immediately!)
sudo passwd pi
```

---

## 4. Installing the LCD Display

> 💡 Skip this section if you're running in windowed mode on a desktop for development.

### 4.1 Attach the Display

Power off the Pi, carefully attach the 3.5" LCD to the GPIO header, then power on.

### 4.2 Install the LCD Driver

For **Kuman SC06** or compatible 3.5" SPI displays:

```bash
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show
sudo ./LCD35-show    # This reboots the Pi
```

After reboot, the Pi desktop should appear on the 3.5" LCD.

> ⚠️ This makes the 3.5" LCD the primary display. To switch back to HDMI later:
> ```bash
> cd ~/LCD-show
> sudo ./LCD-hdmi
> ```

### 4.3 Verify the Display Works

After reboot, you should see the Raspberry Pi desktop on the LCD. If the screen is blank or garbled:

- Try the alternative driver: `sudo ./MHS35-show`
- Check that the display is firmly seated on the GPIO header
- See [Labs README](../labs/README.md) for display calibration and troubleshooting

---

## 5. Installing the Application

### 5.1 Clone the Repository

```bash
ssh pi@<your-pi-ip>
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
```

### 5.2 Install Python Dependencies

On a dedicated Pi (no virtual environment needed):

```bash
pip install -r requirements.txt
```

> ⚠️ **PEP 668 error?** Newer Raspberry Pi OS versions block global pip installs. Add `--break-system-packages`:
> ```bash
> pip install -r requirements.txt --break-system-packages
> ```
> This is safe on a single-purpose Pi.

### 5.3 Verify the Camera

Plug in your USB webcam and check it's detected:

```bash
ls /dev/video*
# Should show /dev/video0 (or similar)
```

---

## 6. Launching the App

### 6.1 Option A — Via SSH (Recommended for Setup & Testing)

This is the best way to get started. You run the app from SSH while it renders on the Pi's LCD:

```bash
ssh pi@<your-pi-ip>
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
python timelapse_touch.py --fullscreen
```

**What happens:**

- The app detects the Pi's desktop session and automatically sets `DISPLAY=:0`
- The UI appears on the Pi's 3.5" LCD
- Logs appear in your SSH terminal — you can see errors, status updates, and debug info
- Stop with `Ctrl+C`

> 💡 **Why SSH?** The 3.5" LCD is too small to type commands or debug. SSH lets you see all output on a full-sized screen while the app runs on the tiny LCD.

### 6.2 Option B — Desktop Shortcut (Daily Use)

Once everything works via SSH, set up a desktop shortcut for tap-to-launch:

```bash
chmod +x install-shortcut.sh
./install-shortcut.sh              # creates a desktop icon
./install-shortcut.sh --autostart  # also starts automatically on boot
```

After running this:

- A **PiTimeLapse Touch** icon appears on the Pi desktop
- Tap the icon on the LCD to launch
- With `--autostart`, the app launches automatically every time the Pi boots

### 6.3 Option C — Windowed Mode (Desktop Development)

On any desktop (Windows, macOS, Linux) without a touchscreen:

```bash
python timelapse_touch.py
```

This opens a 480×320 window you can click with your mouse. Useful for development and testing.

---

## 7. Using the Main Screen

When the app starts, you see the **main screen**:

```
┌──────────────────────────────────────────────────┐
│ PiTimeLapse LED     ✓ 14.2G ~142K  #0            │  ← Header
├────────────────────────┬─────────────────────────┤
│                        │      Last Photo         │
│    Live Camera         │                         │
│    Preview             │    [thumbnail of most   │  ← Split preview
│                        │     recent capture]     │
│                        │                         │
├────────────────────────┴─────────────────────────┤
│   [ START ]    [ SETTINGS ]    [ CLOSE ]         │  ← Buttons
├──────────────────────────────────────────────────┤
│ Status: Ready                    Elapsed: 00:00  │  ← Status bar
└──────────────────────────────────────────────────┘
```

### 7.1 Header Bar

The header shows at a glance:

| Element | Meaning |
|---------|---------|
| **PiTimeLapse** | App title |
| **LED** (green) | USB LED light detected and controllable |
| **LED** (dim gray) | No USB LED detected (check uhubctl installation) |
| **✓** (green) | USB drive connected |
| **✗** (red) | No USB drive — saving to local `./data` folder |
| **14.2G** | Free space on USB drive (when Storage Info is enabled) |
| **~142K** | Estimated remaining photos (when Storage Info is enabled) |
| **#0** | Total photos captured in current session |

### 7.2 Split Preview

The center area is split into two zones:

| Zone | Width | What it shows |
|------|-------|---------------|
| **Live Preview** (left) | ~67% | Live camera feed, updates every 3 seconds |
| **Last Photo** (right) | ~33% | Thumbnail of the most recently captured photo |

If no camera is detected, the live preview shows a "No Camera" placeholder. The thumbnail shows "No Photos" until the first capture.

### 7.3 Buttons

| Button | What it does |
|--------|-------------|
| **START** | Begin capturing photos at the configured interval |
| **STOP** | Appears while capturing — tap to stop the session |
| **SETTINGS** | Open the settings screen (disabled while capturing) |
| **CLOSE** | Exit the application cleanly |

> 💡 You must **STOP** a capture session before opening **SETTINGS**.

### 7.4 Status Bar

The bottom bar shows:

| While... | Left side | Right side |
|----------|-----------|------------|
| **Idle** | `Status: Ready` | `Elapsed: 00:00:00` |
| **Capturing** | `Status: Next: 25s` (countdown to next photo) | `Elapsed: 00:05:30` |
| **Stopped** | `Status: Stopped` | `Elapsed: 00:12:45` |
| **Error** | `Status: Error: <message>` | `Elapsed: 00:03:20` |

> 💡 The countdown timer can be toggled on/off from the Features tab in Settings.

---

## 8. Using the Settings Screen

Tap **SETTINGS** on the main screen (when not capturing) to open the settings form. Settings are organized into **three tabs**.

### 8.1 Switching Tabs

At the top of the settings screen you'll see three tab buttons:

```
┌──────────────┬──────────────┬──────────────┐
│    Camera    │   Features   │     LED      │
└──────────────┴──────────────┴──────────────┘
```

Tap a tab name to switch between them. The **active tab** is highlighted with a green accent line.

### 8.2 Camera Tab

Controls the camera and capture behavior:

| Setting | What it does | Range | Default |
|---------|-------------|-------|---------|
| **Interval (s)** | Seconds between photos | 1 – 3600 | 30 |
| **Quality** | JPEG compression quality | 1 – 100 | 90 |
| **Camera** | Camera device index | 0 – 9 | 0 |
| **Width** | Capture resolution width | 160 – 1920 | 640 |
| **Height** | Capture resolution height | 120 – 1080 | 480 |

**Tips:**

- **Interval** = 30 means one photo every 30 seconds. Set to 1 for rapid capture.
- **Quality** = 90 is a good balance between file size and image quality. Lower values save space.
- **Camera** = 0 is usually your first (or only) webcam. Try 1 if the wrong camera is selected.
- Higher **Width/Height** = better photos but larger files and slower processing.

### 8.3 Features Tab

Toggle optional display features on or off:

| Setting | What it does | Values | Default |
|---------|-------------|--------|---------|
| **Countdown** | Show countdown timer to next capture in the status bar | On / Off | On |
| **Storage Info** | Show free disk space and remaining photos estimate in the header | On / Off | On |

**Tips:**

- Turn off **Countdown** if you prefer a simpler "Capturing..." status message.
- Turn off **Storage Info** for a cleaner header showing just USB status and photo count.

### 8.4 LED Tab

Configure the USB LED flash light. This tab also shows a detection status line:

- **✓ Detected on 1-1.2** (green) — a controllable USB port was found
- **✗ Not detected** (dim) — no controllable port found; install `uhubctl` if needed

| Setting | What it does | Values | Default |
|---------|-------------|--------|---------|
| **LED Flash** | Enable USB LED illumination before each photo | On / Off | On |
| **LED Warmup** | Seconds to wait after LED turns on before capturing | 0 – 5 | 1 |

**Tips:**

- Turn off **LED Flash** if you have no USB LED connected or don't want flash.
- **LED Warmup** = 1 gives the LED time to reach full brightness. Set to 0 for instant capture.
- If the status shows "Not detected", see [Section 10 – USB LED Flash Light](#10-usb-led-flash-light) for setup instructions.

### 8.5 Adjusting Values

Each setting uses stepper controls:

```
  Interval (s)          [–]    30    [+]
```

- Tap **[–]** to decrease the value
- Tap **[+]** to increase the value
- Boolean settings show **On** or **Off** instead of a number

### 8.6 Saving or Discarding

| Button | What it does |
|--------|-------------|
| **SAVE** | Write all settings to `config.yaml` and return to the main screen |
| **BACK** | Discard all changes and return to the main screen |

> 💡 Settings take effect immediately after saving. No restart required.

---

## 9. USB Storage

### 9.1 How It Works

1. **On startup**, the app checks for a connected USB drive
2. **If found** → all photos are saved to the USB drive root
3. **If not found** → photos are saved to the local `./data` folder

### 9.2 Supported Drives

Any USB flash drive or external drive formatted as:

- **FAT32** (recommended — works on all operating systems)
- **exFAT** (for files larger than 4 GB)
- **ext4** (Linux-native, fastest)

### 9.3 Where Photos Are Saved

Photos are organized into session folders with timestamps:

```
USB_DRIVE/
└── session_2026-03-04_17-30-00/
    ├── session.json          # Session metadata
    ├── photo_0001.jpg
    ├── photo_0002.jpg
    ├── photo_0003.jpg
    └── ...
```

### 9.4 Storage Info Display

When **Storage Info** is enabled in the Features tab, the header bar shows:

- **Free space** in gigabytes (e.g., `14.2G`)
- **Estimated remaining photos** (e.g., `~142K`)

The estimate is based on your current resolution and quality settings. Higher resolution or quality = fewer photos per GB.

> 💡 Storage info refreshes every 30 seconds to avoid slowing down the app.

### 9.5 Safely Removing the USB Drive

1. **Stop** any active capture session
2. **Close** the app
3. Unmount the drive: `sudo umount /media/pi/<DRIVE_NAME>`
4. Remove the drive

---

## 10. USB LED Flash Light

The app can control a **USB-powered LED light** by toggling the USB port power on and off before each photo capture. This is ideal for:

- Dark environments (indoor plants, aquariums, night captures)
- Consistent lighting across a time-lapse sequence
- Avoiding ambient light variations

### 10.1 How It Works

Instead of using a serial relay protocol, the app uses **`uhubctl`** to toggle USB port power directly. When the LED's USB port is powered off, the LED turns off. When powered on, it turns on. Simple and reliable.

### 10.2 Requirements

| Item | Notes |
|------|-------|
| **uhubctl** | `sudo apt install uhubctl` — controls USB port power |
| **Any USB LED light** | Ring light, LED strip, desk lamp — anything USB-powered |
| **Root access** | uhubctl needs root permissions (use `sudo` or udev rules) |

> 💡 On a dedicated Pi device, running with `sudo` is the easiest option.

### 10.3 How the Capture Cycle Works

When LED Flash is enabled and a controllable USB port is detected:

```
1. LED ON        ← USB port powered on, light turns on
2. Wait warmup   ← configurable delay (default 1 second)
3. CAPTURE PHOTO ← camera takes the picture
4. LED OFF       ← USB port powered off, light turns off
5. Wait interval ← countdown to next capture
```

If no controllable port is detected, the capture cycle runs normally without steps 1, 2, and 4.

### 10.4 Setup Steps

1. Install uhubctl: `sudo apt install uhubctl`
2. Plug your USB LED light into a USB port on the Pi
3. Run `sudo uhubctl` to verify your USB hub supports per-port power switching
4. The app auto-detects controllable ports on startup
5. Toggle **LED Flash** on/off in Settings → LED tab
6. Adjust **LED Warmup** (0–5 seconds) for your light's warm-up time

### 10.5 Specifying a USB Port

By default, the app auto-detects which USB port to control (`usb_port: auto`). If auto-detection picks the wrong port, you can specify it explicitly in `config.yaml`:

```yaml
led:
  enabled: true
  warmup_seconds: 1.0
  usb_port: "1-1.2"   # explicit hub.port location
```

Run `sudo uhubctl` to list available hubs and ports. The location is shown in the output (e.g., `hub 1-1, port 2` → `usb_port: "1-1.2"`).

### 10.6 Running Without Root

To avoid using `sudo`, create a udev rule:

```bash
# Find your USB hub vendor ID (from uhubctl output)
sudo nano /etc/udev/rules.d/99-uhubctl.rules

# Add this line (adjust idVendor for your hub):
SUBSYSTEM=="usb", ATTR{idVendor}=="2109", MODE="0666"

# Reload rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

> 💡 The header bar shows **LED** in green when a controllable USB port is detected.

---

## 11. Desktop Shortcut & Autostart

### 11.1 Creating a Desktop Shortcut

After testing via SSH, set up a one-tap launcher:

```bash
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
chmod +x install-shortcut.sh
./install-shortcut.sh
```

This creates a **PiTimeLapse Touch** icon on the Pi's desktop. Just tap it on the LCD!

### 11.2 Auto-Launch on Boot

To have the app start automatically every time the Pi powers on:

```bash
./install-shortcut.sh --autostart
```

This copies the desktop entry to `~/.config/autostart/`, so the app launches after the desktop environment loads.

### 11.3 Removing Autostart

```bash
rm ~/.config/autostart/pitimelapse-touch.desktop
```

### 11.4 Removing the Desktop Shortcut

```bash
rm ~/Desktop/pitimelapse-touch.desktop
```

---

## 12. Configuration File Reference

All settings are stored in `config.yaml` in the app directory. You can edit this file manually or use the in-app Settings screen.

### 12.1 Full Configuration File

```yaml
# Touch TimeLapse — Default Configuration

camera:
  mode: opencv          # opencv or picamera2 (future)
  index: 0              # camera device index
  width: 640            # capture resolution width
  height: 480           # capture resolution height

capture:
  interval_seconds: 30  # time between photos (1–3600)
  quality: 90           # JPEG quality (1–100)

preview:
  fps: 6                # live preview frame rate

storage:
  fallback_path: ./data  # used when no USB drive found

led:
  enabled: true          # auto-use USB LED if controllable port found
  warmup_seconds: 1.0    # seconds to wait after LED on, before capture
  usb_port: auto         # "auto" to detect, or explicit like "1-1.2"

display:
  show_countdown: true   # show countdown timer to next photo
  show_storage_info: true # show free space and remaining photos estimate
```

### 12.2 Settings Reference

| Setting | Type | Range | Default | Description |
|---------|------|-------|---------|-------------|
| `camera.mode` | string | `opencv`, `picamera2` | `opencv` | Camera driver to use |
| `camera.index` | integer | 0–9 | `0` | Which camera device to use |
| `camera.width` | integer | 160–1920 | `640` | Capture width in pixels |
| `camera.height` | integer | 120–1080 | `480` | Capture height in pixels |
| `capture.interval_seconds` | integer | 1–3600 | `30` | Seconds between captures |
| `capture.quality` | integer | 1–100 | `90` | JPEG compression quality |
| `preview.fps` | integer | 1–30 | `6` | Live preview refresh rate |
| `storage.fallback_path` | string | any path | `./data` | Where to save if no USB drive |
| `led.enabled` | boolean | `true`/`false` | `true` | Enable USB LED port power control |
| `led.warmup_seconds` | float | 0.0–5.0 | `1.0` | LED warmup delay before capture |
| `led.usb_port` | string | `auto` or port location | `auto` | USB port for LED (`auto` or e.g. `1-1.2`) |
| `display.show_countdown` | boolean | `true`/`false` | `true` | Show countdown in status bar |
| `display.show_storage_info` | boolean | `true`/`false` | `true` | Show storage info in header |

### 12.3 Editing Manually via SSH

```bash
nano ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse/config.yaml
```

Save with `Ctrl+O`, exit with `Ctrl+X`. Changes take effect next time the app starts, or immediately if you save from the in-app Settings screen.

---

## 13. Troubleshooting

### Display Issues

| Problem | Solution |
|---------|----------|
| **App runs but nothing appears on the LCD (via SSH)** | Ensure the Pi desktop is running. The app needs X11 — it auto-sets `DISPLAY=:0`. Verify with: `echo $DISPLAY` on the Pi directly. |
| **Black screen on LCD** | The LCD driver may not be installed. See [Section 4](#4-installing-the-lcd-display). Try `sudo ./MHS35-show` as an alternative driver. |
| **`fbcon not available` error** | SDL 2.32+ removed fbcon support. The app automatically probes `kmsdrm` first. Update to the latest code: `git pull`. |
| **`SDL video driver: dummy` in logs** | The dummy driver renders nothing. Make sure the Pi desktop is running on the LCD — the app needs X11. |
| **Touch not responding** | Verify the touch device exists: `ls /dev/input/touchscreen`. Test with: `evtest /dev/input/event0`. |

### Camera Issues

| Problem | Solution |
|---------|----------|
| **"No Camera" on preview** | Check the camera is plugged in: `ls /dev/video*`. Try changing `camera.index` to `1` in settings. |
| **Camera timeout errors in logs** | USB webcams on the Pi can be slow. The app uses V4L2 optimizations, but some cameras have inherent delays. Try a different USB port or camera. |
| **Blurry or dark photos** | Increase `camera.width` and `camera.height` for better resolution. For dark scenes, enable the LED flash feature. |

### Installation Issues

| Problem | Solution |
|---------|----------|
| **PEP 668 / externally-managed error** | Add `--break-system-packages` to pip: `pip install -r requirements.txt --break-system-packages` |
| **`ModuleNotFoundError: No module named 'pygame'`** | Run `pip install -r requirements.txt` again. On Pi OS Bookworm+, remember `--break-system-packages`. |
| **`ImportError: libopencv` or similar** | Install OpenCV system package: `sudo apt install python3-opencv` |

### Storage Issues

| Problem | Solution |
|---------|----------|
| **USB drive not detected** | Check it's mounted: `lsblk`. Try re-plugging. The drive must be mounted under `/media/`. |
| **"Permission denied" saving photos** | Check write permissions on the USB drive: `touch /media/pi/<DRIVE>/test && rm /media/pi/<DRIVE>/test` |
| **Storage info shows 0** | Storage info refreshes every 30 seconds. Wait a moment, or check if USB is properly mounted. |

### LED Issues

| Problem | Solution |
|---------|----------|
| **LED not detected** | Check uhubctl is installed: `sudo uhubctl`. If not found: `sudo apt install uhubctl`. |
| **Permission denied** | uhubctl needs root. Run app with `sudo` or add a udev rule (see [section 10.6](#106-running-without-root)). |
| **LED turns on but photo is still dark** | Increase `led.warmup_seconds` — the LED may need more time to reach full brightness. |
| **LED stays on after app crash** | Run `sudo uhubctl -l <hub> -p <port> -a off` to manually cut port power. |
| **Wrong USB port detected** | Set `led.usb_port` explicitly in config.yaml (see [section 10.5](#105-specifying-a-usb-port)). |

---

## 14. FAQ

### General

**Q: Can I use this without a touchscreen?**
A: Yes! Run `python timelapse_touch.py` (without `--fullscreen`) on any desktop. Click with your mouse instead of tapping.

**Q: Can I use the Pi Camera Module instead of a USB webcam?**
A: USB webcams via OpenCV are the primary supported mode. Pi Camera Module support via `picamera2` is planned for a future release.

**Q: How many photos can I store?**
A: Depends on resolution and quality. At 640×480 quality 90, each photo is roughly 50–100 KB. A 16 GB USB drive can store approximately 160,000–320,000 photos. Enable **Storage Info** in the Features tab to see live estimates.

**Q: Can I run this 24/7?**
A: Yes! Set up [autostart](#112-auto-launch-on-boot) and the app will launch on every boot. Consider using a quality power supply and adequate cooling for the Pi.

### Camera

**Q: My camera index is wrong — how do I find the right one?**
A: List available cameras: `ls /dev/video*`. The number after `video` is the index (e.g., `/dev/video0` → index 0, `/dev/video2` → index 2). Try each in the Camera tab.

**Q: Can I use multiple cameras?**
A: Only one camera at a time. Change the camera index in Settings to switch between cameras.

### Storage

**Q: What happens if the USB drive fills up?**
A: The app will report a storage error in the status bar and stop capturing. Free up space by removing old session folders from the USB drive.

**Q: Can I use a network drive or NAS?**
A: Not directly. The app looks for USB-mounted drives. You could mount a network share to a local path and set `storage.fallback_path` to that path in `config.yaml`.

### LED

**Q: Do I need the LED feature?**
A: No — it's completely optional. If no controllable USB port is found, the LED feature has zero effect on the app. You can also disable it in the Features tab.

**Q: Can I use any type of light?**
A: Yes — any USB-powered light works (ring light, LED strip, desk lamp). The app controls it by toggling USB port power on and off.

---

## Quick Reference Card

```
┌──────────────────────────────────────────────────┐
│              PiTimeLapse Touch                    │
│                Quick Reference                   │
├──────────────────────────────────────────────────┤
│                                                  │
│  START      Begin time-lapse capture             │
│  STOP       Pause capture session                │
│  SETTINGS   Open settings (Camera / Features)    │
│  CLOSE      Exit the application                 │
│                                                  │
│  Via SSH:   python timelapse_touch.py --fullscreen│
│  Windowed:  python timelapse_touch.py            │
│  Shortcut:  ./install-shortcut.sh                │
│  Autostart: ./install-shortcut.sh --autostart    │
│                                                  │
│  Config:    nano config.yaml                     │
│  Logs:      Watch SSH terminal output            │
│  Camera:    ls /dev/video*                       │
│  USB:       lsblk                                │
│  LED:       sudo uhubctl                        │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

📖 **More resources:**

- [Project README](README.md) — developer reference and project structure
- [Main README](../README.md) — overview of all PiTimeLapse Lab scenarios
- [WebApp TimeLapse](../01-WebApp-TimeLapse/README.md) — browser-based alternative
- [LCD Labs](../labs/README.md) — hands-on touchscreen programming tutorials

---

*Made with ❤️ for makers, learners, and time-lapse enthusiasts!*

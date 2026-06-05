# 👆 Scenario 02 — Touch TimeLapse

> ⚠️ **ARCHIVED SCENARIO**
>
> Scenario 02 is no longer the active touchscreen path. For current Raspberry Pi touchscreen builds, use [**Scenario 03 — DSI Touch TimeLapse**](../../03-DSI-Touch-TimeLapse/README.md).
>
> Scenario 02 remains here as a legacy reference for SPI/GPIO touchscreen workflows.

A **touchscreen GUI time-lapse application** built with Pygame for Raspberry Pi. Tap the screen to start/stop captures — no browser, no keyboard needed.

> 📖 Part of [PiTimeLapse Lab](../README.md). See also: [Scenario 01 — WebApp TimeLapse](../01-WebApp-TimeLapse/README.md) · [**User Manual**](USER_MANUAL.md)

---

## ✨ Features

- 📸 **Capture photos** on a configurable schedule with live preview
- 👆 **Touchscreen GUI** — designed for 3.5" displays (480×320)
- 🔌 **SSH-friendly** — run from SSH and it renders on the LCD automatically
- 💾 **Auto-detects USB storage** — saves to USB drive when available, falls back to local storage
- 🖥️ **Dual mode** — fullscreen on Pi LCD, windowed on desktop for development
- 📷 **OpenCV camera** — works with USB webcams and built-in cameras
- 🎛️ **On-screen controls** — start/stop, settings, close, status display, live preview at 6 fps
- ⚙️ **In-app settings** — tabbed settings screen (Camera + Features) to adjust all parameters from the touchscreen
- 💡 **USB LED light support** — auto-detects USB relay modules to illuminate the scene before each capture
- ⏱️ **Countdown timer** — shows seconds until the next capture (toggleable)
- 📊 **Storage info** — displays free disk space and estimated remaining photos (toggleable)
- 🔘 **Grove Dual Button support** — physical start/stop control (BCM 5/6)
- 🌈 **Grove WS2813 status light** — ring/stick color status and per-capture flash

---

## 🎯 When to Use This

Use **Touch TimeLapse** when you want a **standalone capture station** — plug in a Raspberry Pi with a touchscreen and a camera, and it just works. No network, no browser, no keyboard.

| Use case | This scenario? |
|----------|---------------|
| Field time-lapse (outdoors, no WiFi) | ✅ Perfect |
| Kiosk/exhibit capture station | ✅ Perfect |
| Remote monitoring from your phone | ❌ Use [Scenario 01](../01-WebApp-TimeLapse/) |
| Learning Python web development | ❌ Use [Scenario 01](../01-WebApp-TimeLapse/) |

---

## 🛠️ Hardware Requirements

- **Raspberry Pi** (3B+, 4, or 5)
- **3.5" TFT Touchscreen** — Waveshare, Kuman SC06, or compatible (480×320, SPI)
- **USB webcam** or Pi Camera Module
- **USB storage** (optional) — for saving captures externally

> 💡 **No touchscreen?** You can still run in windowed mode on any desktop for development and testing.

---

## 🚀 Quick Start

### On Raspberry Pi (with touchscreen)

If you want the **short version**, this is the intended flow:

1. **Install Raspberry Pi OS Desktop** and enable SSH in Raspberry Pi Imager
2. **Clone this repo** on the Pi
3. **Run the touch install script** from this folder
4. **Reboot** and tap the shortcut on the LCD

If you want the **full step-by-step version** with cleanup profiles, LCD notes, and recovery commands, use [`../99-InitRPi/rpi-cleanup-ssh-commands.md`](../99-InitRPi/rpi-cleanup-ssh-commands.md).

#### 5-minute setup

#### Step 1 — Flash the OS

- Use **Raspberry Pi Imager**
- Choose **Raspberry Pi OS (Desktop)**
- In the advanced options, enable **SSH** and configure Wi-Fi if needed

#### Step 2 — Connect to the Pi

```bash
ssh pi@<your-pi-ip>
```

#### Step 3 — Clone the repo

```bash
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
```

#### Step 4 — Run the install script

```bash
# first time only: install the LCD driver (reboots the Pi)
bash install.sh --setup-lcd

# after the Pi reboots and you SSH back in
cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
bash install.sh --all
```

#### Step 5 — Reboot

```bash
sudo reboot
```

#### Step 6 — Ready to go

After the final reboot, the Pi is ready to go:

- the LCD desktop should load
- the **PiTimeLapse Touch** shortcut should be on the desktop
- autostart is configured if you used `--all`
- you can still launch manually from SSH for debugging

#### Fast path — dedicated Pi setup

The commands above are the recommended fast path for a dedicated touchscreen Pi.

#### Detailed version

Use the **touch profile** guide in [`../99-InitRPi/rpi-cleanup-ssh-commands.md`](../99-InitRPi/rpi-cleanup-ssh-commands.md) when you want:

- disk-space cleanup before installing
- more cautious step-by-step sequencing
- the full SSH command history for provisioning a dedicated Pi
- a deeper explanation of what each script is doing

```bash
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
pip install -r requirements.txt
```

> 💡 **No virtual environment needed** on a dedicated Pi — install packages globally. If you hit PEP 668 errors, add `--break-system-packages` to the pip command.

There are two ways to launch the app on the Pi:

#### Option A — Test via SSH (recommended first)

SSH into the Pi from another computer so you can see logs and debug issues. The app auto-detects the Pi's desktop session and renders on the LCD:

```bash
ssh pi@<your-pi-ip>
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
python timelapse_touch.py --fullscreen
```

The app will appear on the Pi's touchscreen while you watch the logs in your SSH terminal. This is the best way to test and iterate — you can see errors, stop with `Ctrl+C`, edit config, and relaunch without touching the tiny LCD.

> 💡 **How it works:** When running via SSH, there's no `DISPLAY` environment variable. The app detects the Pi's running desktop session and automatically sets `DISPLAY=:0` so pygame renders on the LCD via X11.

#### Option B — Desktop shortcut (production use)

Once everything works, install a shortcut so you (or anyone) can launch with a single tap on the LCD:

```bash
bash install-shortcut.sh              # creates a desktop icon
bash install-shortcut.sh --autostart  # also launch automatically on boot
```

This creates a **PiTimeLapse Touch** icon on the desktop. Just tap it!

When autostart is enabled, the script also adds a **user-level override** to disable the duplicate `polkit-mate-authentication-agent-1` entry if it exists. This avoids the desktop popup:

`GDBus.Error: org.freedesktop.PolicyKit1.Error.Failed: An authentication agent already exists for the given subject`

> 🎯 **Recommended workflow:** Use **SSH** to install, configure, and test → then run `install-shortcut.sh` to set up one-tap launch for daily use.

### On Desktop (development mode)

```bash
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
pip install -r requirements.txt

# Run in a window for development
python timelapse_touch.py
```

> 💡 **Virtual environment (optional):** On a shared dev machine, create one first to avoid conflicts:
>
> ```bash
> python3 -m venv venv
> source venv/bin/activate    # Windows: venv\Scripts\activate
> ```

---

## 🔧 Configuration

Edit `config.yaml` to customize:

```yaml
camera:
  mode: opencv          # opencv or picamera2 (future)
  index: 0              # camera device index
  width: 640
  height: 480

capture:
  interval_seconds: 30  # time between photos
  quality: 90           # JPEG quality (1-100)

preview:
  fps: 6                # live preview frame rate

storage:
  fallback_path: ./data  # used when no USB drive found

led:
  enabled: true          # auto-use USB LED relay if detected
  warmup_seconds: 1.0    # seconds to wait after LED on, before capture

display:
  show_countdown: true   # show countdown timer to next photo
  show_storage_info: true # show free space and remaining photos estimate
```

### Key Settings

| Setting | What it does | Default |
|---------|-------------|---------|
| `camera.index` | Which camera to use (0 = first, 1 = second) | `0` |
| `capture.interval_seconds` | Seconds between photos | `30` |
| `capture.quality` | JPEG compression quality (1–100) | `90` |
| `preview.fps` | Live preview refresh rate | `6` |
| `storage.fallback_path` | Where to save if no USB drive is found | `./data` |
| `led.enabled` | Auto-use USB LED relay when detected | `true` |
| `led.warmup_seconds` | Seconds between LED on and photo capture | `1.0` |
| `display.show_countdown` | Show countdown timer to next photo during capture | `true` |
| `display.show_storage_info` | Show free disk space and remaining photos estimate | `true` |

---

## 🏗️ Project Structure

```
02-Touch-TimeLapse/
├── timelapse_touch.py     # Main entry point — wires everything together
├── install-shortcut.sh    # Creates desktop shortcut & optional autostart
├── ui_components.py       # Pygame UI widgets (buttons, header, preview, status bar)
├── camera_opencv.py       # Camera capture via OpenCV
├── capture_engine.py      # Background capture loop (LED integration)
├── led_controller.py      # USB LED relay auto-detection and control
├── grove_dual_button.py   # Grove Dual Button GPIO adapter (optional)
├── grove_status_light.py  # Grove WS2813 Ring/Stick status light (optional)
├── storage_manager.py     # File saving & USB detection
├── usb_detector.py        # Auto-detect USB storage devices
├── config.py              # Configuration loading and saving
├── config.yaml            # Default settings
├── requirements.txt       # Python dependencies
├── data/                  # Default local storage for captures
└── tests/                 # Automated tests (pytest)
```

> 📘 Hardware rollout details are in [`GROVE_HARDWARE_PLAN.md`](./GROVE_HARDWARE_PLAN.md).

---

## 🖥️ Usage

```bash
# Via SSH — test on Pi while watching logs in your terminal
ssh pi@<your-pi-ip>
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
python timelapse_touch.py --fullscreen

# Windowed mode — desktop development (macOS/Windows/Linux)
python timelapse_touch.py

# Desktop shortcut — tap the icon on the Pi LCD (after install-shortcut.sh)
```

### On-Screen Controls

- **START** — begin capturing photos at the configured interval
- **STOP** — pause the capture session (replaces START while running)
- **SETTINGS** — open the settings screen to adjust capture parameters
- **CLOSE** — exit the application cleanly
- **Live preview** — always-on camera feed (6 fps) whenever a camera is detected
- **Status bar** — shows capture status, elapsed time, and storage info

### Settings Screen

Tap **SETTINGS** on the main screen (when not capturing) to open the settings form. Settings are organized into two tabs:

#### Camera Tab

- **Interval (s)** — seconds between photos (1–3600)
- **Quality** — JPEG compression (1–100)
- **Camera** — camera device index (0–9)
- **Width / Height** — camera capture resolution

#### Features Tab

- **Countdown** — show/hide the countdown timer to the next capture
- **Storage Info** — show/hide free disk space and remaining photos estimate in the header
- **LED Flash** — enable/disable USB LED relay illumination before each photo
- **LED Warmup** — seconds to wait after turning the LED on before capturing (0–5)

Use the **[–]** and **[+]** stepper buttons to adjust values, then tap **SAVE** to write to `config.yaml` or **BACK** to discard changes.

### Storage Behavior

1. The app checks for a connected USB drive on startup
2. If found → saves photos to the USB drive
3. If not found → falls back to `./data` (configurable in `config.yaml`)

### 💡 USB LED Light

The app can automatically control a **USB relay module** to illuminate the scene before each photo. This is ideal for dark environments or consistent lighting in time-lapse sequences.

**How it works:**

1. On startup, the app scans USB serial ports for relay modules (CH340, FTDI, etc.)
2. If a relay is found and LED is enabled in settings → the capture cycle becomes:
   - **LED ON** → wait warmup (default 1 second) → **capture photo** → **LED OFF**
3. If no relay is detected → normal capture (no delay, no error)

**Supported hardware:**

- LCUS-1 type USB relay modules (most common, ~$3-5)
- SainSmart, HiLetgo, or similar single-channel USB relay boards
- Any USB relay using the standard 0xA0 serial protocol

**Setup:**

```bash
# Install the relay module
pip install pyserial    # already in requirements.txt

# Plug the USB relay into the Pi — it auto-detects as /dev/ttyUSB0
# Connect your LED light to the relay's NO (Normally Open) terminal
```

**Settings (in-app or config.yaml):**

- **LED Light** — On/Off toggle (disable if you don't want LED control)
- **LED Warmup** — seconds to wait after turning on before capture (0–5)

---

## 📺 LCD Setup (First Time)

If you're using a **Kuman SC06** or compatible 3.5" SPI display, you need to install the LCD driver first:

```bash
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show
sudo ./LCD35-show    # Reboots the Pi
```

> ⚠️ This makes the 3.5" LCD the primary display. To switch back to HDMI: `sudo ./LCD-hdmi`

📖 See the [Labs README](../labs/README.md) for detailed LCD setup, calibration, and troubleshooting.

---

## 🧪 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific test
pytest tests/test_camera.py -v
```

---

## 🔌 Dependencies

| Package | Purpose |
|---------|---------|
| `pygame` | Touchscreen GUI rendering |
| `opencv-python-headless` | Camera capture |
| `numpy` | Image array handling |
| `psutil` | System monitoring |
| `pyyaml` | Configuration file parsing |

Install all dependencies:

```bash
pip install -r requirements.txt
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| **App runs but nothing on LCD (via SSH)** | **Ensure the Pi desktop is running on the LCD. The app auto-detects it and sets `DISPLAY=:0`** |
| Black screen on Pi LCD | Check LCD driver install — try `sudo ./MHS35-show` as alternative |
| **`fbcon not available`** | **SDL 2.32+ removed fbcon. Update to latest code — it now tries `kmsdrm` first automatically** |
| **`SDL video driver: dummy`** | **The dummy driver renders nothing. Ensure the Pi desktop is active; the app needs X11 via `DISPLAY=:0`** |
| **PolicyKit popup: `An authentication agent already exists for the given subject`** | **Your desktop session likely has both `lxpolkit` and `polkit-mate-authentication-agent-1`. Run `bash install-shortcut.sh --autostart` once to create the user override that hides the duplicate MATE autostart entry.** |
| No touch response | Verify `/dev/input/touchscreen` exists; run `evtest /dev/input/event0` |
| Camera not found | Check `camera.index` in config.yaml; try `0` or `1` |
| Pygame won't start on Pi | Ensure `SDL_FBDEV=/dev/fb0` is set (the script does this automatically) |
| USB drive not detected | Check drive is mounted; verify with `lsblk` |
| PEP 668 / externally-managed | Add `--break-system-packages` to your pip command |

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) file.

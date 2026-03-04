# 👆 Scenario 02 — Touch TimeLapse

A **touchscreen GUI time-lapse application** built with Pygame for Raspberry Pi. Tap the screen to start/stop captures — no browser, no keyboard needed.

> 📖 Part of [PiTimeLapse Lab](../README.md). See also: [Scenario 01 — WebApp TimeLapse](../01-WebApp-TimeLapse/README.md)

---

## ✨ Features

- 📸 **Capture photos** on a configurable schedule with live preview
- 👆 **Touchscreen GUI** — designed for 3.5" displays (480×320)
- 🔌 **No desktop required** — renders directly to the framebuffer
- 💾 **Auto-detects USB storage** — saves to USB drive when available, falls back to local storage
- 🖥️ **Dual mode** — fullscreen on Pi LCD, windowed on desktop for development
- 📷 **OpenCV camera** — works with USB webcams and built-in cameras
- 🎛️ **On-screen controls** — start/stop, status display, live preview at 6 fps

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

```bash
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
pip install -r requirements.txt

# Run fullscreen on the Pi LCD
python timelapse_touch.py --fullscreen
```

> 💡 **No virtual environment needed** on a dedicated Pi — install packages globally. If you hit PEP 668 errors, add `--break-system-packages` to the pip command.

### Add a Desktop Shortcut (one-time setup)

Want to launch the app with a single tap? Run:

```bash
chmod +x install-shortcut.sh
./install-shortcut.sh              # creates a desktop icon
./install-shortcut.sh --autostart  # also launch automatically on boot
```

This creates a **PiTimeLapse Touch** icon on your desktop. Just tap it!

### On Desktop (development mode)

```bash
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
pip install -r requirements.txt

# Run in a window for development
python timelapse_touch.py
```

> 💡 **Virtual environment (optional):** On a shared dev machine, create one first to avoid conflicts:
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
  interval_seconds: 1   # time between photos
  quality: 90           # JPEG quality (1-100)

preview:
  fps: 6                # live preview frame rate

storage:
  fallback_path: ./data  # used when no USB drive found
```

### Key Settings

| Setting | What it does | Default |
|---------|-------------|---------|
| `camera.index` | Which camera to use (0 = first, 1 = second) | `0` |
| `capture.interval_seconds` | Seconds between photos | `1` |
| `capture.quality` | JPEG compression quality (1–100) | `90` |
| `preview.fps` | Live preview refresh rate | `6` |
| `storage.fallback_path` | Where to save if no USB drive is found | `./data` |

---

## 🏗️ Project Structure

```
02-Touch-TimeLapse/
├── timelapse_touch.py     # Main entry point — wires everything together
├── install-shortcut.sh    # Creates desktop shortcut & optional autostart
├── ui_components.py       # Pygame UI widgets (buttons, header, preview, status bar)
├── camera_opencv.py       # Camera capture via OpenCV
├── capture_engine.py      # Background capture loop
├── storage_manager.py     # File saving & USB detection
├── usb_detector.py        # Auto-detect USB storage devices
├── config.py              # Configuration loading
├── config.yaml            # Default settings
├── requirements.txt       # Python dependencies
├── data/                  # Default local storage for captures
└── tests/                 # Automated tests (pytest)
```

---

## 🖥️ Usage

```bash
# Windowed mode (desktop development)
python timelapse_touch.py

# Fullscreen mode (Pi touchscreen)
python timelapse_touch.py --fullscreen
```

### On-Screen Controls

- **Start** — begin capturing photos at the configured interval
- **Stop** — pause the capture session
- **Live preview** — see what the camera sees in real time (6 fps)
- **Status bar** — shows capture count, interval, and storage location

### Storage Behavior

1. The app checks for a connected USB drive on startup
2. If found → saves photos to the USB drive
3. If not found → falls back to `./data` (configurable in `config.yaml`)

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
| Black screen on Pi LCD | Check LCD driver install — try `sudo ./MHS35-show` as alternative |
| **`fbcon not available`** | **SDL 2.32+ removed fbcon. Update to latest code — it now tries `kmsdrm` first automatically** |
| No touch response | Verify `/dev/input/touchscreen` exists; run `evtest /dev/input/event0` |
| Camera not found | Check `camera.index` in config.yaml; try `0` or `1` |
| Pygame won't start on Pi | Ensure `SDL_FBDEV=/dev/fb0` is set (the script does this automatically) |
| USB drive not detected | Check drive is mounted; verify with `lsblk` |
| PEP 668 / externally-managed | Add `--break-system-packages` to your pip command |

---

## 📄 License

MIT License - see [LICENSE](../LICENSE) file.

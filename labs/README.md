# 🖥️ Waveshare 3.5" RPi LCD (A) — Labs

Hands-on demo applications for the **Waveshare 3.5inch RPi LCD (A)** touchscreen display (480×320, SPI, resistive touch).

## Prerequisites

### 1. Install the LCD Driver

Clone and run the Waveshare LCD driver installer on your Raspberry Pi:

```bash
git clone https://github.com/waveshare/LCD-show.git
cd LCD-show
chmod +x LCD35-show
sudo ./LCD35-show
```

> ⚠️ This will reboot your Pi. After reboot, the 3.5" LCD becomes the primary framebuffer (`/dev/fb1`).

### 2. Install Python Dependencies

```bash
cd labs/
pip install -r requirements.txt
```

### 3. Touchscreen Calibration (Optional)

If touch input feels inaccurate, calibrate with:

```bash
sudo apt-get install xinput-calibrator
DISPLAY=:0.0 xinput_calibrator
```

## Labs Overview

| Lab | Folder | Description |
|-----|--------|-------------|
| 01 | `01-hello-lcd/` | Hello World — text, shapes, and colors on the LCD |
| 02 | `02-touch-demo/` | Interactive touch drawing demo |
| 03 | `03-system-monitor/` | Live CPU, memory, disk, and network stats |
| 04 | `04-image-viewer/` | Browse and display images from a folder |
| 05 | `05-button-ui/` | Touch button UI — mini control panel |

## Running a Lab

Each lab is a standalone Python script. Run from the lab's folder:

```bash
cd labs/01-hello-lcd/
python hello_lcd.py
```

Press **Ctrl+C** or close the window to exit any lab.

## Display Specs

- **Resolution:** 480 × 320 pixels
- **Interface:** SPI (40-pin GPIO header)
- **Touch:** Resistive touchscreen
- **Framebuffer:** `/dev/fb1` (after driver install)
- **Touch device:** `/dev/input/touchscreen`

## Troubleshooting

- **Black screen?** Make sure the LCD driver is installed and the Pi has rebooted.
- **No touch input?** Check that `/dev/input/touchscreen` exists. Re-run `sudo ./LCD35-show`.
- **pygame errors?** Ensure `SDL_FBDEV=/dev/fb1` is set (scripts do this automatically).
- **Running over SSH?** These scripts target the LCD framebuffer directly — no X11 display needed.

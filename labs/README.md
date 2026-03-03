# 🖥️ Kuman 3.5" TFT LCD (SC06) — Labs

Hands-on demo applications for the **Kuman 3.5" TFT LCD SC06** touchscreen display (480×320, SPI, XPT2046 resistive touch).

> **Note:** These labs also work with other generic 3.5" SPI TFT displays that use the ILI9486 controller and XPT2046 touch controller.

## Hardware Specifications

- **Model:** Kuman SC06 (3.5" TFT with Touch Pen)
- **Resolution:** 480 × 320 pixels
- **LCD Controller:** ILI9486 (SPI interface)
- **Touch Controller:** XPT2046 (resistive touchscreen)
- **Interface:** 26-pin GPIO header (directly mounts on Raspberry Pi)
- **Framebuffer:** `/dev/fb1` (after driver install)

## Prerequisites

### 1. Install the LCD Driver (goodtft)

The Kuman SC06 uses the **goodtft/LCD-show** drivers. Clone and run the installer on your Raspberry Pi:

```bash
# Remove any previous LCD driver installations
sudo rm -rf LCD-show

# Clone the goodtft driver repository
git clone https://github.com/goodtft/LCD-show.git
chmod -R 755 LCD-show
cd LCD-show

# Install the 3.5" LCD driver (for Kuman SC06 / MPI3501 compatible)
sudo ./LCD35-show
```

> ⚠️ **This will reboot your Pi.** After reboot, the 3.5" LCD becomes the primary framebuffer (`/dev/fb1`).

#### Alternative Driver (if LCD35-show doesn't work)

Some Kuman displays may need the MHS35 driver instead:

```bash
cd LCD-show
sudo ./MHS35-show
```

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

Save the calibration values to `/etc/X11/xorg.conf.d/99-calibration.conf`.

### 4. Display Rotation (Optional)

To rotate the display (0, 90, 180, or 270 degrees):

```bash
cd LCD-show
sudo ./rotate.sh 90
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

## Driver Compatibility Chart

| Display Model | Driver Command | Notes |
|---------------|----------------|-------|
| Kuman SC06 | `LCD35-show` | Most common, try this first |
| Kuman SC06 (variant) | `MHS35-show` | Alternative if LCD35 doesn't work |
| Generic 3.5" ILI9486 | `LCD35-show` | Works with most ILI9486 displays |
| MHS-3.5" RPi Display | `MHS35-show` | For MHS3528 model |

## Troubleshooting

### Black screen after driver install?

1. Verify the display is properly seated on the GPIO header
2. Check `/dev/fb1` exists: `ls -la /dev/fb*`
3. Try the alternative driver: `sudo ./MHS35-show`

### No touch input?

1. Check touch device exists: `ls -la /dev/input/`
2. Look for `event0` or `touchscreen` symlink
3. Test with: `evtest /dev/input/event0`

### Wrong colors or display artifacts?

The ILI9486 and ILI9341 have different initialization sequences. If colors are wrong, try:

```bash
cd LCD-show
sudo ./MHS35-show
```

### pygame errors?

- Ensure `SDL_FBDEV=/dev/fb1` is set (scripts do this automatically)
- Install pygame: `pip install pygame`

### Running over SSH?

These scripts write directly to the framebuffer — no X11 display needed.

### Touch calibration off?

Run calibration and save values:

```bash
DISPLAY=:0.0 xinput_calibrator
# Copy the output to /etc/X11/xorg.conf.d/99-calibration.conf
```

## Switching Back to HDMI Output

To restore HDMI as the primary display:

```bash
cd LCD-show
sudo ./LCD-hdmi
```

## Resources

- [goodtft/LCD-show GitHub](https://github.com/goodtft/LCD-show)
- [LCD Wiki Documentation](http://www.lcdwiki.com/3.5inch_RPi_Display)

# Lab 03 — System Monitor

Live system stats dashboard for the 3.5" RPi TFT LCD.

## What It Does

Displays real-time metrics on the LCD, refreshing every 2 seconds:

- **CPU temperature** (top-right)
- **CPU usage** with color-coded progress bar
- **Memory usage** (used / total)
- **Disk usage** (used / total)
- **IP address**

Colors shift from green → yellow → red as usage increases.

## Prerequisites

- LCD driver installed (see main labs README):

  ```bash
  cd LCD-show && sudo ./LCD35-show
  ```

- Python 3 with pygame and psutil: `pip install pygame psutil`

## How to Run

```bash
python system_monitor.py
```

## What to Expect

A dark dashboard with live-updating bars and numbers. Tap the bottom-right corner or press **ESC** / **Ctrl+C** to exit.

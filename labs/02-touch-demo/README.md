# Lab 02 — Touch Demo

Interactive drawing demo for the 3.5" RPi TFT LCD touchscreen.

## What It Does

- Tap or drag on the screen to draw colorful circles
- Shows touch coordinates at the bottom
- **Clear** button (top-right) resets the canvas
- **Quit** button (top-left) exits the app

## Prerequisites

- LCD driver installed (see main labs README):

  ```bash
  cd LCD-show && sudo ./LCD35-show
  ```

- Python 3 with pygame: `pip install pygame`

## How to Run

```bash
python touch_demo.py
```

## What to Expect

A dark canvas appears. Touch anywhere to draw circles that cycle through a color palette. Coordinates update live at the bottom of the screen.

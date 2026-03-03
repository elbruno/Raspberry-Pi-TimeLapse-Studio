# Lab 05 — Button UI

A touch-button control panel for the Waveshare 3.5" RPi LCD (A).

## What It Does

Displays a 2×2 grid of touch buttons:

- **LED On/Off** — Toggles a simulated LED indicator (green circle in the header)
- **Take Photo** — Placeholder action that counts "captures" on screen
- **Show IP** — Displays the Pi's current IP address in the status bar
- **Quit** — Exits the application

## Prerequisites

- Waveshare LCD driver installed (`sudo ./LCD35-show`)
- Python 3 with pygame: `pip install pygame`

## How to Run

```bash
python button_ui.py
```

## What to Expect

A dark control-panel screen with four colored buttons. Tap them to trigger actions. The status bar at the bottom shows feedback, and the LED indicator in the header toggles green/gray.

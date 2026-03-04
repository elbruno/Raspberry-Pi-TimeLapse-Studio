# Decisions

Team decisions log. Append-only.

---

## Waveshare LCD Labs Structure

**By:** Linguini (Backend Dev)  
**Date:** 2025-01-20

### Decision
Created a `labs/` folder at repo root with 5 standalone pygame demo apps targeting the Waveshare 3.5" RPi LCD (A) display. Each lab has its own subfolder, Python script, and README.md. A shared `labs/requirements.txt` covers all dependencies (pygame, psutil, Pillow).

### Rationale
- Labs are isolated from the main PiTimeLapse app — no changes to `src/` or core files
- pygame over direct framebuffer writes for simplicity and cross-platform testability
- SDL environment variables (SDL_FBDEV, SDL_MOUSEDEV, SDL_MOUSEDRV) set before pygame import to target the LCD framebuffer
- Numbered folders (01- through 05-) for natural progression from simple to complex

### Impact
- No impact on existing codebase — labs/ is a new standalone directory
- Teams adding new labs should follow the same pattern: numbered subfolder, standalone script, README.md

---

## Touch TimeLapse Backend Module Layout

**By:** Linguini (Backend Dev)  
**Date:** 2025-07-24

### Decision

Created 7 backend files for the Touch TimeLapse standalone app in `02 - Touch TimeLapse/`:

| File | Purpose |
|------|---------|
| `config.yaml` | Default settings (camera, capture, preview, storage) |
| `config.py` | YAML loading with deep-merge defaults + dot-notation accessor + validation |
| `usb_detector.py` | Auto-detect first USB drive via psutil; cross-platform (Linux + Windows) |
| `camera_opencv.py` | Simplified OpenCVCamera ported from WebApp; same interface pattern |
| `storage_manager.py` | Session dataclass + StorageManager (create/resume/save/load/crash-recovery) |
| `capture_engine.py` | Background-thread capture loop with thread-safe status and retry logic |
| `requirements.txt` | pygame, psutil, opencv-python-headless, numpy, pyyaml |

### Key Design Choices

1. **Session dataclass in storage_manager.py** — keeps modules independently importable without a separate `models.py`. The Touch app is simpler than the WebApp and doesn't need the same level of separation.

2. **camera_opencv.open(camera_index, width, height)** — takes `camera_index` as first parameter (vs WebApp which stores it in `__init__`). This lets the GUI swap cameras at runtime without recreating the object.

3. **CaptureEngine uses interruptible sleep** — `threading.Event.wait(0.25)` loop instead of `time.sleep(interval)`. Stop latency is ≤250ms, important for responsive touchscreen UI.

4. **USB fallback is silent** — no dialog, no user prompt. Auto-picks first USB drive, falls back to `./data`. Confirmed by Bruno for V1.

### Rationale

- All modules follow the optional-dependency pattern (try/except import with `*_AVAILABLE` flag)
- Thread safety via `threading.Lock` on all shared state in CaptureEngine
- Session metadata saved after every capture for crash recovery
- Validated that all modules import and run on Windows; Linux/Pi paths are conditional

### Impact

- Frontend (GUI) team can import these modules directly
- No changes to existing `01 - WebApp TimeLapse/` code
- Future picamera2 support: add `camera_picamera2.py` and update `camera.mode` in config.yaml

---

## User Directive: Graphical Touch App Design Decisions

**By:** Bruno Capuano (via Copilot)  
**Date:** 2026-03-04T20:56:24Z

### Decision

1. Use lower FPS (6 FPS) for camera preview — power efficiency over smoothness
2. Auto-pick the first USB drive with storage — no selection dialog
3. Detect and resume sessions after crash — not always-new-session
4. Include config.yaml with sensible defaults — must work out of the box
5. Start with USB camera (OpenCV) only; add picamera2 support later via config.yaml camera_mode setting

### Rationale

User design decisions for the new graphical timelapse touch app — captured for team memory.

---

## Touch TimeLapse UI Architecture

**By:** Colette (Frontend Dev)  
**Date:** 2025-07-25

### Decision

Created `02 - Touch TimeLapse/ui_components.py` and `02 - Touch TimeLapse/timelapse_touch.py` as the pygame-based UI for the Touch TimeLapse app.

### Key Design Choices

1. **Defensive imports** — all backend modules (`camera_opencv`, `capture_engine`, `storage_manager`, `usb_detector`, `config`) are wrapped in `try/except ImportError` with `*_AVAILABLE` flags. The UI can launch and render even when Linguini's modules aren't present yet.

2. **SDL framebuffer pattern** — reused the `DISPLAY` env-var detection from labs (`os.environ.setdefault`) so the app auto-targets `/dev/fb0` on headless Pi or uses normal windowing on desktop.

3. **6 FPS preview loop** — `pygame.time.Clock.tick(6)` governs the main loop, balancing smooth preview with power efficiency.

4. **Start/Stop button swap** — only one action button is visible at a time (`btn.visible` toggle) to prevent accidental double-taps.

5. **Session resume** — on init, checks `storage.find_interrupted_session()` and resumes it on next Start press.

### Rationale

- Matches lab conventions (SDL env, monospace font, 480×320, dark theme)
- Defensive imports allow parallel development with Linguini
- Single-button-visible pattern is safer for touch interfaces

### Impact

- Linguini's backend modules must match the documented interfaces (exact method signatures in the task spec)
- Desktop testing: `python timelapse_touch.py` (windowed); Pi: `python timelapse_touch.py --fullscreen`

---

## LED Controller Rewrite: Serial Relay → USB Port Power Control

**By:** Linguini (Backend Dev)  
**Date:** 2026-03-05

### Decision

Rewrote `02-Touch-TimeLapse/led_controller.py` to control USB LED lights by toggling USB port power instead of sending serial relay commands.

### Changes Made

1. **Complete rewrite of led_controller.py**
   - Removed pyserial dependency and LCUS-1 protocol commands
   - Added uhubctl-based USB port power control (Linux only)
   - Auto-detection skips system devices (cameras, storage, HID)
   - Explicit port configuration via `led.usb_port` in config.yaml

2. **Config updates**
   - Added `led.usb_port: "auto"` to config.py defaults
   - Documented usb_port option in config.yaml

3. **Interface preserved**
   - All public methods unchanged: `detect()`, `turn_on()`, `turn_off()`, `close()`, `is_available()`, `port_name`
   - `__init__()` now accepts optional `usb_port` parameter with default "auto"
   - Backward compatible with existing code (timelapse_touch.py, capture_engine.py)

### Rationale

- Original serial relay approach (LCUS-1 protocol via pyserial) didn't work — the USB LED stayed always on regardless of commands sent
- User has a simple USB-powered LED that just needs power on/off, no special protocol
- uhubctl is standard on Raspberry Pi (`sudo apt install uhubctl`)
- USB port power control is the "native" way to control power on Pi

### Technical Approach

Uses the `uhubctl` tool to control per-port USB power:
- `uhubctl -l {hub} -p {port} -a on -r 0` — turn port on
- `uhubctl -l {hub} -p {port} -a off -r 0` — turn port off
- Auto-detection parses uhubctl output, builds list of controllable ports with devices
- Skips ports with system devices (USB hubs, mass storage, cameras, video, input/HID, audio)
- Linux only — gracefully returns False on Windows/macOS

### Impact

- **No changes needed** to timelapse_touch.py, capture_engine.py, or ui_components.py
- Existing code continues to work (backward compatible __init__ signature)
- Future improvement: pass `config["led"]["usb_port"]` when creating LEDController in timelapse_touch.py
- User must install uhubctl: `sudo apt install uhubctl`
- May need to run with sudo or configure udev rules for non-root access

---

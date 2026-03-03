# Linguini — History

## Project Context
**Project:** PiTimeLapse Lab — Cross-platform Flask time-lapse capture app
**Stack:** Python, Flask, OpenCV, picamera2 (optional), YAML, Pillow
**User:** Bruno Capuano

## Key Architecture
- CaptureScheduler runs in dedicated thread, uses threading.Event for signaling
- Captures on interval, retries 3x on failure, respects duration/storage limits
- Camera interface: is_available(), open(w,h), capture() → ndarray|None, close()
- Optional imports: try/except with AVAILABLE flags, logger.warning for install hints
- Config validation: AppConfig.validate() returns list of errors
- Session metadata saved as session.json after each capture

## Learnings
- Created `labs/` folder with 5 Waveshare 3.5" RPi LCD (A) demo apps using pygame + framebuffer
- Pattern for LCD apps: set SDL_FBDEV/SDL_MOUSEDEV/SDL_MOUSEDRV env vars before importing pygame
- Screen resolution: 480×320, SPI interface, resistive touch, driver from waveshare/LCD-show
- Labs dependencies: pygame, psutil, Pillow (separate requirements.txt in labs/)
- Each lab is standalone with its own README.md — beginner-friendly with extensive comments
- Key paths: labs/01-hello-lcd/, labs/02-touch-demo/, labs/03-system-monitor/, labs/04-image-viewer/, labs/05-button-ui/

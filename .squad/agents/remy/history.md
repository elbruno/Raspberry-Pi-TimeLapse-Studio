# Remy — History

## Project Context
**Project:** PiTimeLapse Lab — Cross-platform Flask time-lapse capture app
**Stack:** Python, Flask, OpenCV, picamera2 (optional), YAML, Pillow
**User:** Bruno Capuano

## Key Architecture
- Camera abstraction: `OpenCVCamera` and `PiCamera2Camera` share interface (is_available, open, capture, close)
- Optional dependency pattern: try/except import with `*_AVAILABLE` flags
- Background capture: `CaptureScheduler` in dedicated thread with `threading.Event`
- Config validation returns error list (not exceptions)
- Session metadata persisted as `session.json` after each capture

## Learnings

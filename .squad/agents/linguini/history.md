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

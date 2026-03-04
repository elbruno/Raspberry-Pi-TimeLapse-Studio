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
- Built backend modules for `02 - Touch TimeLapse/` standalone app: config.py, config.yaml, usb_detector.py, camera_opencv.py, storage_manager.py, capture_engine.py, requirements.txt
- Touch TimeLapse uses same camera interface as WebApp (is_available/open/capture/close) but `open()` takes camera_index as first arg for flexibility
- Session dataclass lives in storage_manager.py (not a separate models.py) — keeps the module self-contained and independently importable
- USB detection via psutil: Linux looks for /dev/sd* not at / or /boot; Windows uses ctypes GetDriveTypeW for removable check; auto-fallback to ./data
- CaptureEngine uses threading.Event for interruptible sleep (0.25s granularity) so stop is near-instant
- Crash recovery: find_interrupted_session() scans for session.json files without end_time, resume_session() continues numbering
- Config uses deep-merge of loaded YAML over built-in DEFAULTS dict, with dot-notation accessor (get_config_value)
- validate_config() returns list of error strings (same pattern as WebApp's AppConfig.validate())

## Touch TimeLapse Build Integration (2026-03-04)
- **Colette** built defensive UI importing all backend modules with try/except and `*_AVAILABLE` flags — backend modules match exact interface contracts
- **Alfredo** wrote comprehensive test suite (7 files, 50+ cases) validating interfaces — all 67/67 tests passing
- Orchestration logs: `.squad/orchestration-log/2026-03-04T2100-{linguini,colette,alfredo}.md`
- All decisions merged into `.squad/decisions.md` with deduplication


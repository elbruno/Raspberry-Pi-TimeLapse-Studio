# Colette — History

## Project Context
**Project:** PiTimeLapse Lab — Cross-platform Flask time-lapse capture app
**Stack:** Python, Flask, OpenCV, picamera2 (optional), YAML, Pillow
**User:** Bruno Capuano

## Key Architecture
- Flask app in `src/pitimelapse/app.py` with web routes
- Templates in `templates/`, static assets in `static/`
- Web UI polls status while capture thread runs in background
- Status updates use thread-safe locks in CaptureScheduler

## Learnings

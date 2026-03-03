# PiTimeLapse Lab — Squad Team

## Project Context

**Project:** PiTimeLapse Lab — Cross-platform Flask web app for time-lapse photo capture
**Stack:** Python, Flask, OpenCV, picamera2 (optional), YAML config, Pillow
**Platform:** Raspberry Pi (primary), Windows/macOS/Linux (cross-platform)
**User:** Bruno Capuano
**Created:** 2026-03-03

## Members

| Name | Role | Specialties | Emoji |
|------|------|-------------|-------|
| Remy | Lead | Architecture, code review, Pi hardware decisions, cross-platform design | 🏗️ |
| Colette | Frontend Dev | Flask templates, web UI, status dashboard, static assets | ⚛️ |
| Linguini | Backend Dev | Capture engine, camera drivers, threading, storage, config | 🔧 |
| Alfredo | Tester | Tests, edge cases, hardware mocking, validation, CI | 🧪 |
| Scribe | Session Logger | Memory, decisions, session logs | 📋 |
| Ralph | Work Monitor | Work queue, backlog, keep-alive | 🔄 |

## Tech Stack Details

- **Web Framework:** Flask (routes in `src/pitimelapse/app.py`)
- **Camera:** OpenCV (primary, cross-platform), picamera2 (Raspberry Pi only)
- **Config:** YAML (`config.yaml`) → `AppConfig` dataclass (`src/pitimelapse/config.py`)
- **Storage:** File-based sessions with `session.json` metadata
- **Background Capture:** Threading with `CaptureScheduler` (`src/pitimelapse/capture.py`)
- **Entry Point:** `main.py` (CLI commands: validate, sessions, cleanup, serve)
- **Tests:** pytest (`tests/`)
- **Key Pattern:** Optional dependency handling (try/except import with availability flags)

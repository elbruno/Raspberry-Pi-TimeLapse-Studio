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

### 2025-01-20: Graphical Desktop App Planning
**Task:** Analyzed existing codebase and proposed architecture for new touch-screen time-lapse app  
**Key Findings:**
- 60-70% of existing code is reusable (camera, storage patterns, session model)
- pygame is optimal GUI framework (already validated in Lab 05, framebuffer support)
- USB auto-detection via psutil (cross-platform, lightweight)
- OpenCV → pygame conversion requires BGR→RGB + transpose for surface display
- 1-second capture interval requires <200ms save time to maintain timing

**Architecture Decisions:**
- Main thread: pygame event loop (30 FPS) with live preview
- Background thread: 1-second capture loop with thread-safe status
- USB detection at startup (no hot-plug support in V1)
- Fallback to `./data` if no USB drive found

**Deliverable:** Comprehensive plan document at `.squad/graphical-app-plan.md` (25KB, ~600 lines)  
**Timeline:** 4-day implementation (USB detection → camera integration → UI → testing)  
**Open Questions:** Camera preview FPS, USB selection UI, session resume behavior, config file necessity, Pi Camera support

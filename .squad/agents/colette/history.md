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
- Labs 02-05 in `labs/` use a consistent SDL env-var pattern (set before `import pygame`), framebuffer detection via `DISPLAY` env var, 480×320 screen, and `SysFont("monospace")` — adopted all of these in the Touch TimeLapse app.
- Button class in lab 05 uses `time.time()` for 150ms press feedback — reused the same approach with rounded corners and darker-shade feedback in `ui_components.py`.
- Backend modules (`camera_opencv`, `capture_engine`, `storage_manager`, `usb_detector`, `config`) are imported defensively with `try/except ImportError` and `*_AVAILABLE` flags so the UI can run standalone for testing even without Linguini's modules.
- `PreviewArea` converts BGR→RGB via numpy slice (`frame[:, :, ::-1]`) and uses `pygame.surfarray.make_surface` + `smoothscale` for aspect-ratio-preserving preview.
- Touch TimeLapse layout: 40px header, flexible preview, 100px button row, 30px status bar — totals 480×320 for Pi touchscreen.

## Touch TimeLapse Build Integration (2026-03-04)
- **Linguini** built 7 backend modules (~1100 lines) matching exact interface contracts specified in task
- **Alfredo** wrote comprehensive test suite validating all backend interfaces — all 67/67 tests passing
- Orchestration logs: `.squad/orchestration-log/2026-03-04T2100-{linguini,colette,alfredo}.md`
- All decisions merged into `.squad/decisions.md` with deduplication


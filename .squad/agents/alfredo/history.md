# Alfredo — History

## Project Context
**Project:** PiTimeLapse Lab — Cross-platform Flask time-lapse capture app
**Stack:** Python, Flask, OpenCV, picamera2 (optional), YAML, Pillow
**User:** Bruno Capuano

## Key Architecture
- Tests in `tests/` using pytest
- Existing tests: test_config.py, test_storage.py, test_utils.py
- Run with: `pytest tests/ -v`
- Camera hardware must be mocked for CI
- Config validation returns error lists — test both valid and invalid inputs

## Learnings

### Touch TimeLapse Test Suite (2025-03-04)
- Created full test suite in `02 - Touch TimeLapse/tests/` with 7 files (conftest + 5 test modules + __init__)
- Tests cover: usb_detector, camera_opencv, storage_manager, config, capture_engine
- All hardware (cv2, psutil) mocked with unittest.mock.patch — CI-friendly, no camera needed
- Used pytest tmp_path for all file system tests, parametrize for validation ranges
- Capture engine tests use short intervals (0.1s) and threading for fast execution
- Tests are written against specified interfaces — production code being built in parallel by Linguini/Colette
- Total: ~50 test cases across 5 modules

## Touch TimeLapse Build Integration (2026-03-04)
- **Linguini** built 7 backend modules (~1100 lines) matching interface contracts
- **Colette** built UI layer (2 files, ~690 lines) with defensive imports and 6 FPS preview
- Fixed 12 test/code interface mismatches during parallel development
- All 67/67 tests passing — validates both backend and UI integration
- Orchestration logs: `.squad/orchestration-log/2026-03-04T2100-{linguini,colette,alfredo}.md`
- All decisions merged into `.squad/decisions.md` with deduplication


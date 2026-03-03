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

# Routing Rules

## Signal → Agent Mapping

| Signal / Domain | Primary Agent | Secondary |
|----------------|---------------|-----------|
| Architecture, design decisions, code review | Remy | — |
| Flask routes, templates, HTML/CSS, web UI | Colette | Remy (review) |
| Camera code, capture engine, threading, storage | Linguini | Remy (review) |
| Config, models, CLI commands, utils | Linguini | Remy (review) |
| Pi hardware, picamera2, GPIO, system integration | Linguini | Remy (architecture) |
| Tests, test infrastructure, mocking, coverage | Alfredo | — |
| Documentation, guides, troubleshooting | Remy | Colette (UI docs) |
| Cross-platform compatibility | Remy | Linguini |
| Static assets, images, CSS, JavaScript | Colette | — |
| Validation, error handling patterns | Linguini | Alfredo (test coverage) |

## File → Agent Mapping

| Path Pattern | Agent |
|-------------|-------|
| `src/pitimelapse/app.py` | Colette |
| `templates/**`, `static/**` | Colette |
| `src/pitimelapse/capture.py` | Linguini |
| `src/pitimelapse/camera_*.py` | Linguini |
| `src/pitimelapse/storage.py` | Linguini |
| `src/pitimelapse/config.py` | Linguini |
| `src/pitimelapse/models.py` | Linguini |
| `src/pitimelapse/overlay.py` | Linguini |
| `src/pitimelapse/utils.py` | Linguini |
| `main.py` | Linguini |
| `config.yaml` | Linguini |
| `tests/**` | Alfredo |
| `docs/**` | Remy |
| `requirements.txt` | Remy |

# Decision: Waveshare LCD Labs Structure

**By:** Linguini (Backend Dev)
**Date:** 2025-01-20

## Decision
Created a `labs/` folder at repo root with 5 standalone pygame demo apps targeting the Waveshare 3.5" RPi LCD (A) display. Each lab has its own subfolder, Python script, and README.md. A shared `labs/requirements.txt` covers all dependencies (pygame, psutil, Pillow).

## Rationale
- Labs are isolated from the main PiTimeLapse app — no changes to `src/` or core files
- pygame over direct framebuffer writes for simplicity and cross-platform testability
- SDL environment variables (SDL_FBDEV, SDL_MOUSEDEV, SDL_MOUSEDRV) set before pygame import to target the LCD framebuffer
- Numbered folders (01- through 05-) for natural progression from simple to complex

## Impact
- No impact on existing codebase — labs/ is a new standalone directory
- Teams adding new labs should follow the same pattern: numbered subfolder, standalone script, README.md

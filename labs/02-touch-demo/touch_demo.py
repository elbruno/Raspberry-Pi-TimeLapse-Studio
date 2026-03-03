#!/usr/bin/env python3
"""
Lab 02 — Touch Demo
====================
Interactive touch drawing demo for the 3.5" RPi LCD.
Tap or drag on the screen to draw colored circles. A "Clear" button
in the top-right corner resets the canvas. Touch coordinates are shown
at the bottom of the screen.

Hardware: Kuman SC06 3.5" TFT LCD (480x320, ILI9486, XPT2046 touch)
          Also works with other SPI displays using goodtft/LCD-show drivers
Run:      python touch_demo.py
Exit:     Ctrl+C or tap the X button
"""

import os
import sys
import random

# ---------------------------------------------------------------------------
# SDL environment — set BEFORE importing pygame.
# If running in desktop (X11), use normal display.
# If running in console (no DISPLAY), use framebuffer directly.
# ---------------------------------------------------------------------------
if not os.environ.get("DISPLAY"):
    # Console mode — write directly to LCD framebuffer
    # fb0 = ILI9486 LCD (confirmed via /sys/class/graphics/fb0/name)
    os.environ["SDL_VIDEODRIVER"] = "fbcon"
    os.environ["SDL_FBDEV"] = "/dev/fb0"
    os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
    os.environ["SDL_MOUSEDRV"] = "TSLIB"
    print("Running in framebuffer mode (console) on /dev/fb0")
else:
    # Desktop mode — use X11 display
    print(f"Running in X11 mode (DISPLAY={os.environ['DISPLAY']})")

import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
FPS = 60

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (60, 60, 60)
RED = (220, 50, 50)
DARK_BG = (15, 15, 30)

# Circle radius range when drawing
MIN_RADIUS = 8
MAX_RADIUS = 16

# Clear button rectangle (top-right corner)
CLEAR_BTN = pygame.Rect(390, 5, 80, 30)
# Quit button
QUIT_BTN = pygame.Rect(5, 5, 60, 30)

# Palette of colors to cycle through
PALETTE = [
    (255, 100, 100),
    (100, 255, 100),
    (100, 100, 255),
    (255, 255, 100),
    (255, 100, 255),
    (100, 255, 255),
    (255, 180, 50),
]


def main():
    """Main loop: handle touch events, draw circles, show coordinates."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lab 02 — Touch Demo")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("monospace", 16)
    font_btn = pygame.font.SysFont("monospace", 14, bold=True)

    # Canvas surface (separate so we can clear it without losing UI)
    canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    canvas.fill(DARK_BG)

    last_touch = None  # (x, y) of most recent touch
    color_index = 0
    drawing = False  # True while mouse/touch is held down

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                # Check clear button
                if CLEAR_BTN.collidepoint(pos):
                    canvas.fill(DARK_BG)
                    last_touch = None
                # Check quit button
                elif QUIT_BTN.collidepoint(pos):
                    running = False
                else:
                    drawing = True
                    last_touch = pos
                    radius = random.randint(MIN_RADIUS, MAX_RADIUS)
                    pygame.draw.circle(canvas, PALETTE[color_index % len(PALETTE)], pos, radius)
                    color_index += 1

            elif event.type == pygame.MOUSEMOTION and drawing:
                pos = event.pos
                last_touch = pos
                radius = random.randint(MIN_RADIUS - 2, MAX_RADIUS - 4)
                pygame.draw.circle(canvas, PALETTE[color_index % len(PALETTE)], pos, max(radius, 4))

            elif event.type == pygame.MOUSEBUTTONUP:
                drawing = False

        # --- Render ---
        screen.blit(canvas, (0, 0))

        # Clear button
        pygame.draw.rect(screen, GRAY, CLEAR_BTN, border_radius=5)
        clear_text = font_btn.render("Clear", True, WHITE)
        screen.blit(clear_text, (CLEAR_BTN.x + 12, CLEAR_BTN.y + 6))

        # Quit button
        pygame.draw.rect(screen, RED, QUIT_BTN, border_radius=5)
        quit_text = font_btn.render("Quit", True, WHITE)
        screen.blit(quit_text, (QUIT_BTN.x + 8, QUIT_BTN.y + 6))

        # Coordinate bar at bottom
        coord_str = f"Touch: ({last_touch[0]}, {last_touch[1]})" if last_touch else "Touch the screen to draw"
        coord_surface = font.render(coord_str, True, WHITE)
        pygame.draw.rect(screen, BLACK, (0, SCREEN_HEIGHT - 24, SCREEN_WIDTH, 24))
        screen.blit(coord_surface, (10, SCREEN_HEIGHT - 20))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        print("\nExited.")

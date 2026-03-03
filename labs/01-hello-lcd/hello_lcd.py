#!/usr/bin/env python3
"""
Lab 01 — Hello LCD
==================
Display "Hello World" on the 3.5" RPi LCD using pygame.
Shows colored background, text, and basic shapes (rectangle, circle, line).

Hardware: Kuman SC06 3.5" TFT LCD (480x320, ILI9486, XPT2046 touch)
          Also works with other SPI displays using goodtft/LCD-show drivers
Run:      python hello_lcd.py
Exit:     Ctrl+C or close the window
"""

import os
import sys
import time

# ---------------------------------------------------------------------------
# SDL environment — must be set BEFORE importing pygame so it targets the
# LCD framebuffer instead of HDMI.
# ---------------------------------------------------------------------------
os.environ["SDL_FBDEV"] = "/dev/fb1"
os.environ["SDL_MOUSEDEV"] = "/dev/input/touchscreen"
os.environ["SDL_MOUSEDRV"] = "TSLIB"

import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
FPS = 30

# Colors (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
BLUE = (50, 100, 220)
YELLOW = (255, 220, 50)
DARK_BLUE = (20, 30, 80)


def main():
    """Set up pygame, draw shapes and text, then wait for quit."""
    pygame.init()

    # Create the display surface — on the Pi this opens on /dev/fb1
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lab 01 — Hello LCD")
    clock = pygame.time.Clock()

    # Load fonts
    font_large = pygame.font.SysFont("monospace", 36, bold=True)
    font_small = pygame.font.SysFont("monospace", 18)

    running = True
    while running:
        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # --- Drawing ---
        screen.fill(DARK_BLUE)

        # Rectangle
        pygame.draw.rect(screen, RED, (20, 20, 140, 80), border_radius=10)

        # Circle
        pygame.draw.circle(screen, GREEN, (360, 60), 50)

        # Horizontal line
        pygame.draw.line(screen, YELLOW, (20, 130), (460, 130), 3)

        # Main title
        title_surface = font_large.render("Hello, LCD!", True, WHITE)
        title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, 170))
        screen.blit(title_surface, title_rect)

        # Subtitle
        sub_surface = font_small.render("Waveshare 3.5\" RPi LCD (A)", True, YELLOW)
        sub_rect = sub_surface.get_rect(center=(SCREEN_WIDTH // 2, 210))
        screen.blit(sub_surface, sub_rect)

        # Info line
        info_surface = font_small.render(f"480x320 | SPI | pygame {pygame.version.ver}", True, WHITE)
        info_rect = info_surface.get_rect(center=(SCREEN_WIDTH // 2, 260))
        screen.blit(info_surface, info_rect)

        # Footer
        footer_surface = font_small.render("Press ESC or Ctrl+C to exit", True, (150, 150, 150))
        footer_rect = footer_surface.get_rect(center=(SCREEN_WIDTH // 2, 300))
        screen.blit(footer_surface, footer_rect)

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

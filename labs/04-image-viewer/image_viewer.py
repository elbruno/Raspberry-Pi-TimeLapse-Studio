#!/usr/bin/env python3
"""
Lab 04 — Image Viewer
=====================
Display images from a folder on the Waveshare 3.5" RPi LCD (A).
Tap the left half of the screen for previous image, right half for next.
Images are scaled to fit 480×320 while preserving aspect ratio.

Usage:
    python image_viewer.py                  # uses ./images/ folder
    python image_viewer.py /path/to/photos  # custom folder

Hardware: Waveshare 3.5inch RPi LCD (A), 480x320, SPI
Exit:     Ctrl+C or press ESC
"""

import os
import sys
import glob

# SDL framebuffer configuration
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

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (120, 120, 120)
DARK_BG = (10, 10, 15)

# Supported image extensions
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff")


def find_images(folder: str) -> list:
    """Return sorted list of image file paths in the given folder."""
    images = []
    for ext in IMAGE_EXTS:
        images.extend(glob.glob(os.path.join(folder, f"*{ext}")))
        images.extend(glob.glob(os.path.join(folder, f"*{ext.upper()}")))
    return sorted(set(images))


def scale_image(surface: pygame.Surface, max_w: int, max_h: int) -> pygame.Surface:
    """Scale a surface to fit within max_w × max_h, preserving aspect ratio."""
    w, h = surface.get_size()
    ratio = min(max_w / w, max_h / h)
    new_w = int(w * ratio)
    new_h = int(h * ratio)
    return pygame.transform.smoothscale(surface, (new_w, new_h))


def main():
    """Main loop: load images, handle navigation, render."""
    # Determine image folder from command-line arg or default
    if len(sys.argv) > 1:
        image_folder = sys.argv[1]
    else:
        image_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lab 04 — Image Viewer")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("monospace", 16)
    font_big = pygame.font.SysFont("monospace", 22, bold=True)

    # Find images
    images = find_images(image_folder)
    if not images:
        print(f"No images found in: {image_folder}")
        print("Place .jpg/.png files in the 'images/' subfolder, or pass a folder path.")
        print("Creating a placeholder message on screen...")

    current_index = 0
    cached_surface = None  # scaled pygame.Surface for current image

    def load_current():
        """Load and scale the current image, return surface or None."""
        if not images:
            return None
        try:
            img = pygame.image.load(images[current_index])
            return scale_image(img, SCREEN_WIDTH, SCREEN_HEIGHT)
        except pygame.error as e:
            print(f"Error loading {images[current_index]}: {e}")
            return None

    cached_surface = load_current()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_RIGHT and images:
                    current_index = (current_index + 1) % len(images)
                    cached_surface = load_current()
                elif event.key == pygame.K_LEFT and images:
                    current_index = (current_index - 1) % len(images)
                    cached_surface = load_current()

            elif event.type == pygame.MOUSEBUTTONDOWN and images:
                x, _y = event.pos
                if x > SCREEN_WIDTH // 2:
                    # Tap right half → next
                    current_index = (current_index + 1) % len(images)
                else:
                    # Tap left half → previous
                    current_index = (current_index - 1) % len(images)
                cached_surface = load_current()

        # --- Draw ---
        screen.fill(DARK_BG)

        if cached_surface:
            # Center the image on screen
            iw, ih = cached_surface.get_size()
            x = (SCREEN_WIDTH - iw) // 2
            y = (SCREEN_HEIGHT - ih) // 2
            screen.blit(cached_surface, (x, y))

            # Image counter overlay
            counter = font.render(f"{current_index + 1} / {len(images)}", True, WHITE)
            # Semi-transparent background for readability
            pygame.draw.rect(screen, BLACK, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 24, 100, 24))
            screen.blit(counter, (SCREEN_WIDTH - 95, SCREEN_HEIGHT - 22))

            # Filename
            name = os.path.basename(images[current_index])
            name_surf = font.render(name[:40], True, GRAY)
            pygame.draw.rect(screen, BLACK, (0, SCREEN_HEIGHT - 24, name_surf.get_width() + 10, 24))
            screen.blit(name_surf, (5, SCREEN_HEIGHT - 22))
        else:
            # No images — show message
            msg1 = font_big.render("No Images Found", True, WHITE)
            msg2 = font.render(f"Folder: {image_folder}", True, GRAY)
            msg3 = font.render("Add .jpg/.png files to view them", True, GRAY)
            screen.blit(msg1, msg1.get_rect(center=(SCREEN_WIDTH // 2, 120)))
            screen.blit(msg2, msg2.get_rect(center=(SCREEN_WIDTH // 2, 170)))
            screen.blit(msg3, msg3.get_rect(center=(SCREEN_WIDTH // 2, 200)))

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

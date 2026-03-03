#!/usr/bin/env python3
"""
Lab 05 — Button UI
==================
A simple touch-button control panel for the Waveshare 3.5" RPi LCD (A).

Buttons:
  • LED On/Off — Toggles a simulated LED indicator on screen
  • Take Photo  — Placeholder that shows a "captured!" flash
  • Show IP     — Displays the current IP address
  • Quit        — Exits the application

Hardware: Waveshare 3.5inch RPi LCD (A), 480x320, SPI, resistive touch
Run:      python button_ui.py
Exit:     Ctrl+C or tap the Quit button
"""

import os
import sys
import socket
import time

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

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BG = (15, 18, 30)
HEADER_BG = (20, 40, 80)
GREEN = (50, 200, 80)
RED = (200, 50, 50)
BLUE = (50, 100, 220)
ORANGE = (230, 150, 30)
GRAY = (70, 70, 90)
LIGHT_GRAY = (160, 160, 160)
YELLOW = (255, 230, 50)
LED_ON_COLOR = (50, 255, 50)
LED_OFF_COLOR = (60, 60, 60)

# Button layout — 2 columns × 2 rows
BUTTON_W = 200
BUTTON_H = 80
MARGIN = 20
START_X = (SCREEN_WIDTH - 2 * BUTTON_W - MARGIN) // 2
START_Y = 60


def get_ip_address() -> str:
    """Get the primary IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "No network"


class Button:
    """A simple rectangular touch button."""

    def __init__(self, x, y, w, h, label, color):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.color = color
        self.pressed = False  # visual feedback state
        self.press_time = 0

    def draw(self, surface, font):
        """Render the button with optional press animation."""
        color = self.color
        # Brief highlight on press
        if self.pressed and time.time() - self.press_time < 0.15:
            color = tuple(min(c + 60, 255) for c in self.color)
        else:
            self.pressed = False

        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, WHITE, self.rect, width=2, border_radius=10)
        text = font.render(self.label, True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        surface.blit(text, text_rect)

    def is_clicked(self, pos) -> bool:
        """Check if a position is inside this button."""
        if self.rect.collidepoint(pos):
            self.pressed = True
            self.press_time = time.time()
            return True
        return False


def main():
    """Main loop: render buttons, handle touch, show status."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lab 05 — Button UI")
    clock = pygame.time.Clock()

    font = pygame.font.SysFont("monospace", 18, bold=True)
    font_status = pygame.font.SysFont("monospace", 16)
    font_title = pygame.font.SysFont("monospace", 20, bold=True)

    # Create buttons in a 2×2 grid
    btn_led = Button(START_X, START_Y, BUTTON_W, BUTTON_H, "LED On/Off", BLUE)
    btn_photo = Button(START_X + BUTTON_W + MARGIN, START_Y, BUTTON_W, BUTTON_H, "Take Photo", ORANGE)
    btn_ip = Button(START_X, START_Y + BUTTON_H + MARGIN, BUTTON_W, BUTTON_H, "Show IP", GREEN)
    btn_quit = Button(START_X + BUTTON_W + MARGIN, START_Y + BUTTON_H + MARGIN, BUTTON_W, BUTTON_H, "Quit", RED)

    buttons = [btn_led, btn_photo, btn_ip, btn_quit]

    # State
    led_on = False
    status_msg = "Ready"
    status_time = time.time()
    photo_count = 0

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos

                if btn_led.is_clicked(pos):
                    led_on = not led_on
                    status_msg = f"LED {'ON' if led_on else 'OFF'}"
                    status_time = time.time()

                elif btn_photo.is_clicked(pos):
                    photo_count += 1
                    status_msg = f"Photo #{photo_count} captured!"
                    status_time = time.time()

                elif btn_ip.is_clicked(pos):
                    ip = get_ip_address()
                    status_msg = f"IP: {ip}"
                    status_time = time.time()

                elif btn_quit.is_clicked(pos):
                    running = False

        # --- Draw ---
        screen.fill(DARK_BG)

        # Header
        pygame.draw.rect(screen, HEADER_BG, (0, 0, SCREEN_WIDTH, 44))
        title = font_title.render("Control Panel", True, WHITE)
        screen.blit(title, (10, 10))

        # LED indicator in header
        led_color = LED_ON_COLOR if led_on else LED_OFF_COLOR
        pygame.draw.circle(screen, led_color, (SCREEN_WIDTH - 30, 22), 12)
        pygame.draw.circle(screen, WHITE, (SCREEN_WIDTH - 30, 22), 12, 2)
        led_label = font_status.render("LED", True, LIGHT_GRAY)
        screen.blit(led_label, (SCREEN_WIDTH - 70, 14))

        # Buttons
        for btn in buttons:
            btn.draw(screen, font)

        # Status bar at bottom
        pygame.draw.rect(screen, (25, 25, 40), (0, SCREEN_HEIGHT - 30, SCREEN_WIDTH, 30))
        # Fade status message after 5 seconds
        if time.time() - status_time < 5:
            status_surf = font_status.render(status_msg, True, YELLOW)
        else:
            status_surf = font_status.render(status_msg, True, GRAY)
        screen.blit(status_surf, (10, SCREEN_HEIGHT - 26))

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

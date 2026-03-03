#!/usr/bin/env python3
"""
Lab 03 — System Monitor
========================
Display live system stats on the 3.5" RPi LCD:
  • CPU temperature
  • CPU usage (%)
  • Memory usage
  • Disk usage
  • IP address

Auto-refreshes every 2 seconds.

Hardware: Kuman SC06 3.5" TFT LCD (480x320, ILI9486, XPT2046 touch)
          Also works with other SPI displays using goodtft/LCD-show drivers
Run:      python system_monitor.py
Exit:     Ctrl+C or tap the screen quit area
"""

import os
import sys
import socket
import time

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
import psutil

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SCREEN_WIDTH = 480
SCREEN_HEIGHT = 320
REFRESH_INTERVAL = 2  # seconds

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (80, 220, 80)
YELLOW = (255, 220, 50)
RED = (220, 60, 60)
CYAN = (80, 220, 220)
DARK_BG = (10, 12, 25)
BAR_BG = (40, 40, 60)
HEADER_BG = (20, 40, 80)


def get_cpu_temp() -> str:
    """Read CPU temperature. Returns string like '42.3°C' or 'N/A'."""
    try:
        # Raspberry Pi thermal zone
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_c = int(f.read().strip()) / 1000.0
        return f"{temp_c:.1f}°C"
    except (FileNotFoundError, ValueError):
        # Fallback: try psutil sensors
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                first = list(temps.values())[0]
                return f"{first[0].current:.1f}°C"
        except Exception:
            pass
    return "N/A"


def get_ip_address() -> str:
    """Get the primary IP address of the Pi."""
    try:
        # Connect to a public DNS to determine local IP (no data sent)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "No network"


def color_for_percent(value: float) -> tuple:
    """Return green/yellow/red based on usage percentage."""
    if value < 60:
        return GREEN
    elif value < 85:
        return YELLOW
    return RED


def draw_bar(surface, x, y, width, height, percent, color):
    """Draw a progress bar with background and filled portion."""
    pygame.draw.rect(surface, BAR_BG, (x, y, width, height), border_radius=4)
    fill_w = int(width * min(percent, 100) / 100)
    if fill_w > 0:
        pygame.draw.rect(surface, color, (x, y, fill_w, height), border_radius=4)


def main():
    """Main loop: poll system stats and render to LCD."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Lab 03 — System Monitor")
    clock = pygame.time.Clock()

    font_title = pygame.font.SysFont("monospace", 22, bold=True)
    font_label = pygame.font.SysFont("monospace", 18)
    font_value = pygame.font.SysFont("monospace", 18, bold=True)
    font_small = pygame.font.SysFont("monospace", 14)

    last_update = 0  # force immediate first update
    stats = {}

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Tap bottom-right corner to quit
                if event.pos[0] > 400 and event.pos[1] > 280:
                    running = False

        # --- Refresh stats every REFRESH_INTERVAL seconds ---
        now = time.time()
        if now - last_update >= REFRESH_INTERVAL:
            last_update = now
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            stats = {
                "cpu_temp": get_cpu_temp(),
                "cpu_pct": psutil.cpu_percent(interval=0),
                "mem_pct": mem.percent,
                "mem_used": mem.used // (1024 * 1024),
                "mem_total": mem.total // (1024 * 1024),
                "disk_pct": disk.percent,
                "disk_used": disk.used // (1024 ** 3),
                "disk_total": disk.total // (1024 ** 3),
                "ip": get_ip_address(),
            }

        if not stats:
            continue

        # --- Draw ---
        screen.fill(DARK_BG)

        # Header
        pygame.draw.rect(screen, HEADER_BG, (0, 0, SCREEN_WIDTH, 36))
        title = font_title.render("System Monitor", True, CYAN)
        screen.blit(title, (10, 6))
        temp_surf = font_value.render(stats["cpu_temp"], True, YELLOW)
        screen.blit(temp_surf, (SCREEN_WIDTH - temp_surf.get_width() - 10, 8))

        y = 50  # vertical cursor

        # CPU Usage
        cpu_color = color_for_percent(stats["cpu_pct"])
        screen.blit(font_label.render("CPU", True, WHITE), (10, y))
        screen.blit(font_value.render(f"{stats['cpu_pct']:5.1f}%", True, cpu_color), (380, y))
        draw_bar(screen, 70, y + 2, 300, 18, stats["cpu_pct"], cpu_color)
        y += 40

        # Memory
        mem_color = color_for_percent(stats["mem_pct"])
        screen.blit(font_label.render("MEM", True, WHITE), (10, y))
        mem_str = f"{stats['mem_used']}M / {stats['mem_total']}M"
        screen.blit(font_value.render(f"{stats['mem_pct']:5.1f}%", True, mem_color), (380, y))
        draw_bar(screen, 70, y + 2, 300, 18, stats["mem_pct"], mem_color)
        screen.blit(font_small.render(mem_str, True, (150, 150, 150)), (70, y + 22))
        y += 55

        # Disk
        disk_color = color_for_percent(stats["disk_pct"])
        screen.blit(font_label.render("DSK", True, WHITE), (10, y))
        disk_str = f"{stats['disk_used']}G / {stats['disk_total']}G"
        screen.blit(font_value.render(f"{stats['disk_pct']:5.1f}%", True, disk_color), (380, y))
        draw_bar(screen, 70, y + 2, 300, 18, stats["disk_pct"], disk_color)
        screen.blit(font_small.render(disk_str, True, (150, 150, 150)), (70, y + 22))
        y += 55

        # IP Address
        screen.blit(font_label.render("IP", True, WHITE), (10, y))
        screen.blit(font_value.render(stats["ip"], True, GREEN), (70, y))
        y += 35

        # Footer
        footer = font_small.render("Tap bottom-right to quit | Refreshes every 2s", True, (100, 100, 100))
        screen.blit(footer, (10, SCREEN_HEIGHT - 20))

        pygame.display.flip()
        clock.tick(10)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pygame.quit()
        print("\nExited.")

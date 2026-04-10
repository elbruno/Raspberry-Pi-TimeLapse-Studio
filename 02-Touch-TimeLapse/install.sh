#!/usr/bin/env bash
# -----------------------------------------------------------
# PiTimeLapse Touch — full install script for Raspberry Pi
# -----------------------------------------------------------
# Installs all system packages and Python dependencies needed
# to run the touchscreen time-lapse app.
#
# Usage:
#   chmod +x install.sh
#   ./install.sh                # standard install
#   ./install.sh --with-led     # also install uhubctl for USB LED control
#   ./install.sh --autostart    # install + create desktop shortcut + autostart
#   ./install.sh --all          # all of the above (LED + autostart, no LCD)
#   ./install.sh --setup-lcd    # first-time LCD driver setup (reboots Pi!)
# -----------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WITH_LED=0
AUTOSTART=0
SETUP_LCD=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)        WITH_LED=1; AUTOSTART=1; shift ;;
    --with-led)   WITH_LED=1;  shift ;;
    --autostart)  AUTOSTART=1; shift ;;
    --setup-lcd)  SETUP_LCD=1; shift ;;
    -h|--help)
      echo "Usage: ./install.sh [--all] [--with-led] [--autostart] [--setup-lcd]"
      echo "  --all         Install everything (LED + desktop shortcut + autostart)"
      echo "  --with-led    Install uhubctl for USB LED flash control"
      echo "  --autostart   Create desktop shortcut + autostart on boot"
      echo "  --setup-lcd   First-time 3.5\" SPI LCD driver setup (Kuman SC06 / ILI9486)"
      echo "                ⚠  Reboots the Pi! Run './install.sh --all' after reboot."
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

# ------------------------------------------------------------------
# 0. LCD driver setup (first-time only — reboots at the end)
# ------------------------------------------------------------------
if [[ $SETUP_LCD -eq 1 ]]; then
  echo "== LCD Driver Setup (Kuman SC06 / 3.5\" SPI ILI9486) =="
  echo

  # Check if already installed
  if [[ -f /boot/firmware/overlays/tft35a.dtbo ]] && grep -q "dtoverlay=tft35a" /boot/firmware/config.txt 2>/dev/null; then
    echo "LCD driver overlay already installed."
    echo "If the screen still doesn't work, try: cd /tmp/LCD-show && sudo ./LCD35-show"
    echo
  else
    LCD_SHOW_DIR="/tmp/LCD-show"
    if [[ -d "$LCD_SHOW_DIR" ]]; then
      echo "Updating existing LCD-show repository..."
      cd "$LCD_SHOW_DIR" && git pull 2>/dev/null || true
    else
      echo "Cloning goodtft/LCD-show driver..."
      git clone https://github.com/goodtft/LCD-show.git "$LCD_SHOW_DIR"
    fi
    chmod -R 755 "$LCD_SHOW_DIR"
    cd "$LCD_SHOW_DIR"

    echo
    echo "Installing LCD35 driver..."
    echo "⚠  This will:"
    echo "   • Switch display mode to X11 (required for SPI LCD)"
    echo "   • Configure SPI and the tft35a overlay"
    echo "   • Reboot the Pi"
    echo
    echo "After reboot, run the full install:"
    echo "  cd ${SCRIPT_DIR} && ./install.sh --all"
    echo

    sudo ./LCD35-show
    # LCD35-show reboots — script won't reach here
    exit 0
  fi
fi

echo "== PiTimeLapse Touch — Install =="
echo

# ------------------------------------------------------------------
# 1. System packages
# ------------------------------------------------------------------
echo "[1/4] Installing system dependencies..."
sudo apt update

# Core: SDL2 for pygame display, python3-pip for pip installs
PKGS=(
  python3-pip
  python3-dev
  libsdl2-2.0-0
  libsdl2-image-2.0-0
  libsdl2-mixer-2.0-0
  libsdl2-ttf-2.0-0
)

# Optional: uhubctl for toggling USB port power (LED flash light)
if [[ $WITH_LED -eq 1 ]]; then
  PKGS+=(uhubctl)
fi

sudo apt install -y "${PKGS[@]}"
echo

# ------------------------------------------------------------------
# 2. Python packages
# ------------------------------------------------------------------
echo "[2/4] Installing Python dependencies..."
pip3 install -r "${SCRIPT_DIR}/requirements.txt" --break-system-packages
echo

# ------------------------------------------------------------------
# 3. Verify installation
# ------------------------------------------------------------------
echo "[3/4] Verifying imports..."
FAILED=0

python3 -c "import pygame; print(f'  pygame {pygame.ver} ✓')" 2>/dev/null || { echo "  pygame ✗"; FAILED=1; }
python3 -c "import cv2; print(f'  opencv {cv2.__version__} ✓')" 2>/dev/null || { echo "  opencv ✗"; FAILED=1; }
python3 -c "import numpy; print(f'  numpy {numpy.__version__} ✓')" 2>/dev/null || { echo "  numpy ✗"; FAILED=1; }
python3 -c "import psutil; print(f'  psutil {psutil.__version__} ✓')" 2>/dev/null || { echo "  psutil ✗"; FAILED=1; }
python3 -c "import yaml; print(f'  pyyaml ✓')" 2>/dev/null || { echo "  pyyaml ✗"; FAILED=1; }

if [[ $WITH_LED -eq 1 ]]; then
  if command -v uhubctl >/dev/null 2>&1; then
    echo "  uhubctl ✓"
  else
    echo "  uhubctl ✗ (LED control will not work)"
    FAILED=1
  fi
fi

echo

# Check LCD driver status
if [[ -f /boot/firmware/overlays/tft35a.dtbo ]] && grep -q "dtoverlay=tft35a" /boot/firmware/config.txt 2>/dev/null; then
  echo "  LCD driver (tft35a) ✓"
else
  echo "  LCD driver ✗ (3.5\" SPI LCD will show white screen!)"
  echo "    → Run: ./install.sh --setup-lcd"
  FAILED=1
fi

if [[ $FAILED -eq 1 ]]; then
  echo
  echo "⚠  Some dependencies failed to install. Check the output above."
else
  echo
  echo "All dependencies installed successfully."
fi

# ------------------------------------------------------------------
# 4. Optional: desktop shortcut + autostart
# ------------------------------------------------------------------
if [[ $AUTOSTART -eq 1 ]]; then
  echo
  echo "[4/4] Setting up desktop shortcut + autostart..."
  bash "${SCRIPT_DIR}/install-shortcut.sh" --autostart
else
  echo
  echo "[4/4] Skipping desktop shortcut (use --autostart to enable)."
fi

echo
echo "========================================="
echo "Done! Run the app with:"
echo "  cd ${SCRIPT_DIR}"
echo "  python3 timelapse_touch.py --fullscreen"
echo
if [[ $AUTOSTART -eq 1 ]]; then
  echo "Reboot recommended so autostart takes effect:"
  echo "  sudo reboot"
else
  echo "A reboot is recommended to ensure display"
  echo "drivers pick up the new SDL2 libraries:"
  echo "  sudo reboot"
fi
echo "========================================="

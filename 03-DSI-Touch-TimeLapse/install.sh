#!/usr/bin/env bash
# -----------------------------------------------------------
# PiTimeLapse DSI Touch — install script for Raspberry Pi
# -----------------------------------------------------------
# Installs dependencies needed to run Scenario 03 with a DSI
# display (for example Freenove 7" DSI panel).
#
# Usage:
#   chmod +x install.sh
#   ./install.sh                # standard install
#   ./install.sh --shortcut     # create desktop shortcut only (no autostart)
#   ./install.sh --autostart    # create desktop shortcut + autostart
#   ./install.sh --all          # dependencies + desktop shortcut (no autostart)
# -----------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SHORTCUT=0
AUTOSTART=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)        SHORTCUT=1; shift ;;
    --shortcut)   SHORTCUT=1; shift ;;
    --autostart)  SHORTCUT=1; AUTOSTART=1; shift ;;
    -h|--help)
      echo "Usage: ./install.sh [--all] [--shortcut] [--autostart]"
      echo "  --all         Install dependencies + desktop shortcut (no autostart)"
      echo "  --shortcut    Create desktop shortcut only"
      echo "  --autostart   Create desktop shortcut + autostart on boot"
      echo "                and disable the duplicate MATE PolicyKit agent when present"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

echo "== PiTimeLapse DSI Touch — Install =="
echo

# ------------------------------------------------------------------
# 1. System packages
# ------------------------------------------------------------------
echo "[1/4] Installing system dependencies..."
sudo apt update

PKGS=(
  python3-pip
  python3-dev
  libsdl2-2.0-0
  libsdl2-image-2.0-0
  libsdl2-mixer-2.0-0
  libsdl2-ttf-2.0-0
)

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

echo
if [[ $FAILED -eq 1 ]]; then
  echo "⚠  Some dependencies failed to install. Check the output above."
else
  echo "All dependencies installed successfully."
fi

# ------------------------------------------------------------------
# 4. Optional: desktop shortcut / autostart
# ------------------------------------------------------------------
if [[ $SHORTCUT -eq 1 ]]; then
  echo
  if [[ $AUTOSTART -eq 1 ]]; then
    echo "[4/4] Setting up desktop shortcut + autostart..."
    bash "${SCRIPT_DIR}/install-shortcut.sh" --autostart
  else
    echo "[4/4] Setting up desktop shortcut (autostart remains disabled)..."
    bash "${SCRIPT_DIR}/install-shortcut.sh"
  fi
else
  echo
  echo "[4/4] Skipping desktop shortcut (use --shortcut or --autostart to enable)."
fi

echo
echo "========================================="
echo "Done! Run the app with:"
echo "  cd ${SCRIPT_DIR}"
echo "  python3 timelapse_touch.py --fullscreen"
echo
if [[ $AUTOSTART -eq 0 ]]; then
  echo "Autostart is disabled by default."
  echo "To enable it later:"
  echo "  bash install.sh --autostart"
  echo
fi
echo "Notes for DSI displays:"
echo "  • No SPI LCD driver script is required for Freenove DSI displays"
echo "  • Ensure Raspberry Pi OS Desktop is running on the DSI panel"
echo
if [[ $AUTOSTART -eq 1 ]]; then
  echo "Reboot recommended so autostart takes effect:"
  echo "  sudo reboot"
else
  echo "A reboot is recommended after first install:"
  echo "  sudo reboot"
fi
echo "========================================="

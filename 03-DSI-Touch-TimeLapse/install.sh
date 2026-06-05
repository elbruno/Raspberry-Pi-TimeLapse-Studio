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
#   ./install.sh --with-camera-daemon
#   ./install.sh --with-camera-daemon-autostart
# -----------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SHORTCUT=0
AUTOSTART=0
CAMERA_DAEMON=0
CAMERA_DAEMON_AUTOSTART=0
CAMERA_DAEMON_SERVICE=""

detect_camera_daemon_service() {
  if sudo systemctl list-unit-files --type=service | grep -q '^v4l2rtspserver\.service'; then
    echo "v4l2rtspserver"
    return 0
  fi
  if sudo systemctl list-unit-files --type=service | grep -q '^v4l2rtsp\.service'; then
    echo "v4l2rtsp"
    return 0
  fi
  echo ""
  return 1
}

install_local_v4l2rtspserver_service() {
  local unit_path="/etc/systemd/system/pitimelapse-v4l2rtspserver.service"
  local video_device="/dev/video0"

  if [[ ! -e "$video_device" ]]; then
    # Keep default /dev/video0 in unit; this warning helps users tune if needed.
    echo "  Warning: ${video_device} not found right now; service may need device tuning later."
  fi

  sudo tee "$unit_path" >/dev/null << 'EOF'
[Unit]
Description=PiTimeLapse camera daemon (v4l2rtspserver)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/v4l2rtspserver -W 640 -H 480 -F 15 /dev/video0
Restart=always
RestartSec=3
StartLimitIntervalSec=120
StartLimitBurst=10

[Install]
WantedBy=multi-user.target
EOF

  sudo systemctl daemon-reload
  CAMERA_DAEMON_SERVICE="pitimelapse-v4l2rtspserver"
  echo "  Installed local service unit: ${unit_path}"
}

verify_rtsp_endpoint() {
  python3 - << 'PY'
import socket

host = "127.0.0.1"
port = 8554
try:
    with socket.create_connection((host, port), timeout=1.5):
        print("  RTSP endpoint reachable at rtsp://127.0.0.1:8554/unicast ✓")
except Exception:
    print("  RTSP endpoint not reachable yet (expected if service is disabled or still starting)")
PY
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)        SHORTCUT=1; CAMERA_DAEMON=1; shift ;;
    --shortcut)   SHORTCUT=1; shift ;;
    --autostart)  SHORTCUT=1; AUTOSTART=1; shift ;;
    --with-camera-daemon) CAMERA_DAEMON=1; shift ;;
    --with-camera-daemon-autostart) CAMERA_DAEMON=1; CAMERA_DAEMON_AUTOSTART=1; shift ;;
    -h|--help)
      echo "Usage: ./install.sh [--all] [--shortcut] [--autostart] [--with-camera-daemon] [--with-camera-daemon-autostart]"
      echo "  --all         Install dependencies + desktop shortcut (no autostart)"
      echo "  --shortcut    Create desktop shortcut only"
      echo "  --autostart   Create desktop shortcut + autostart on boot"
      echo "  --with-camera-daemon            Install v4l2rtspserver + diagnostics"
      echo "  --with-camera-daemon-autostart  Install camera daemon packages and enable"
      echo "                                  v4l2rtspserver service at boot"
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

if [[ $CAMERA_DAEMON -eq 1 ]]; then
  PKGS+=(
    v4l2-utils
    v4l2rtspserver
  )
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

echo
if [[ $FAILED -eq 1 ]]; then
  echo "⚠  Some dependencies failed to install. Check the output above."
else
  echo "All dependencies installed successfully."
fi

if [[ $CAMERA_DAEMON -eq 1 ]]; then
  echo
  echo "Camera daemon prerequisites installed."
  echo "  RTSP URL default: rtsp://127.0.0.1:8554/unicast"
  if CAMERA_DAEMON_SERVICE="$(detect_camera_daemon_service)"; then
    echo "  Detected system service unit: ${CAMERA_DAEMON_SERVICE}.service"
  else
    echo "  No distro-provided service unit detected; can create local service when autostart is requested."
  fi

  if [[ $CAMERA_DAEMON_AUTOSTART -eq 1 ]]; then
    if [[ -z "$CAMERA_DAEMON_SERVICE" ]]; then
      echo "No packaged daemon service found; creating local service unit..."
      install_local_v4l2rtspserver_service
    fi

    echo "Enabling ${CAMERA_DAEMON_SERVICE} autostart..."
    sudo systemctl enable --now "${CAMERA_DAEMON_SERVICE}" || true
    if sudo systemctl is-active --quiet "${CAMERA_DAEMON_SERVICE}"; then
      echo "  ${CAMERA_DAEMON_SERVICE} is active ✓"
    else
      echo "  ${CAMERA_DAEMON_SERVICE} is not active"
      echo "  Check: sudo systemctl status ${CAMERA_DAEMON_SERVICE}"
    fi
  fi

  verify_rtsp_endpoint
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
if [[ $CAMERA_DAEMON -eq 1 ]]; then
  echo "  • Camera daemon prerequisites installed (v4l2rtspserver + v4l-utils)"
fi
echo
if [[ $AUTOSTART -eq 1 ]]; then
  echo "Reboot recommended so autostart takes effect:"
  echo "  sudo reboot"
else
  echo "A reboot is recommended after first install:"
  echo "  sudo reboot"
fi
echo "========================================="

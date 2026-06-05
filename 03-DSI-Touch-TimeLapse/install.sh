#!/usr/bin/env bash
# -----------------------------------------------------------
# PiTimeLapse DSI Touch — install script for Raspberry Pi
# -----------------------------------------------------------
# Usage:
#   chmod +x install.sh
#   ./install.sh
#   ./install.sh --shortcut
#   ./install.sh --autostart
#   ./install.sh --all
#   ./install.sh --with-camera-daemon
#   ./install.sh --with-camera-daemon-autostart
#   ./install.sh --with-camera-daemon --build-camera-daemon-from-source
# -----------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SHORTCUT=0
AUTOSTART=0
CAMERA_DAEMON=0
CAMERA_DAEMON_AUTOSTART=0
BUILD_CAMERA_DAEMON_FROM_SOURCE=0
CAMERA_DAEMON_SERVICE=""
CAMERA_DAEMON_BIN_AVAILABLE=0

package_available() {
	local pkg="$1"
	apt-cache show "$pkg" >/dev/null 2>&1
}

detect_camera_daemon_service() {
	if sudo systemctl list-unit-files --type=service | grep -q '^v4l2rtspserver\.service'; then
		echo "v4l2rtspserver"
		return 0
	fi
	if sudo systemctl list-unit-files --type=service | grep -q '^v4l2rtsp\.service'; then
		echo "v4l2rtsp"
		return 0
	fi
	if sudo systemctl list-unit-files --type=service | grep -q '^pitimelapse-v4l2rtspserver\.service'; then
		echo "pitimelapse-v4l2rtspserver"
		return 0
	fi
	echo ""
	return 1
}

install_camera_daemon_from_source() {
	local tmp_dir="/tmp/v4l2rtspserver-build"

	echo "  Installing build dependencies for source build..."
	sudo apt install -y git cmake build-essential pkg-config liblog4cpp5-dev liblivemedia-dev

	echo "  Cloning and building v4l2rtspserver from source..."
	rm -rf "$tmp_dir"
	git clone --depth 1 https://github.com/mpromonet/v4l2rtspserver.git "$tmp_dir"
	cmake -S "$tmp_dir" -B "$tmp_dir/build" -DCMAKE_BUILD_TYPE=Release
	cmake --build "$tmp_dir/build" -j2
	sudo cmake --install "$tmp_dir/build"
	rm -rf "$tmp_dir"
}

install_local_v4l2rtspserver_service() {
	local unit_path="/etc/systemd/system/pitimelapse-v4l2rtspserver.service"
	local video_device="/dev/video0"
	local daemon_bin=""

	daemon_bin="$(command -v v4l2rtspserver || true)"
	if [[ -z "$daemon_bin" ]]; then
		daemon_bin="/usr/local/bin/v4l2rtspserver"
	fi

	if [[ ! -x "$daemon_bin" ]]; then
		echo "  Error: v4l2rtspserver binary not found at ${daemon_bin}"
		echo "  Install the daemon first, then re-run with --with-camera-daemon-autostart"
		return 1
	fi

	if [[ ! -e "$video_device" ]]; then
		echo "  Warning: ${video_device} not found right now; service may need device tuning later."
	fi

	sudo tee "$unit_path" >/dev/null << EOF
[Unit]
Description=PiTimeLapse camera daemon (v4l2rtspserver, USB)
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=120
StartLimitBurst=10

[Service]
Type=simple
ExecStart=${daemon_bin} -W 640 -H 480 -F 15 ${video_device}
Restart=always
RestartSec=3

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
		--all) SHORTCUT=1; CAMERA_DAEMON=1; shift ;;
		--shortcut) SHORTCUT=1; shift ;;
		--autostart) SHORTCUT=1; AUTOSTART=1; shift ;;
		--with-camera-daemon) CAMERA_DAEMON=1; shift ;;
		--with-camera-daemon-autostart) CAMERA_DAEMON=1; CAMERA_DAEMON_AUTOSTART=1; shift ;;
		--build-camera-daemon-from-source) BUILD_CAMERA_DAEMON_FROM_SOURCE=1; shift ;;
		-h|--help)
			echo "Usage: ./install.sh [--all] [--shortcut] [--autostart] [--with-camera-daemon] [--with-camera-daemon-autostart] [--build-camera-daemon-from-source]"
			echo "  --all                              Install dependencies + desktop shortcut (no autostart)"
			echo "  --shortcut                         Create desktop shortcut only"
			echo "  --autostart                        Create desktop shortcut + app autostart on boot"
			echo "  --with-camera-daemon               Install camera daemon prerequisites and diagnostics"
			echo "  --with-camera-daemon-autostart     Install/enable camera daemon service at boot"
			echo "  --build-camera-daemon-from-source  Build/install v4l2rtspserver from source when apt package is unavailable"
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
		v4l-utils
	)

	if package_available v4l2rtspserver; then
		PKGS+=(v4l2rtspserver)
	else
		echo "  Warning: package 'v4l2rtspserver' is not available in current apt repositories."
		echo "           You can continue with direct camera mode, or use --build-camera-daemon-from-source."
	fi
fi

sudo apt install -y "${PKGS[@]}"
echo

if [[ $CAMERA_DAEMON -eq 1 && $BUILD_CAMERA_DAEMON_FROM_SOURCE -eq 1 ]]; then
	if ! command -v v4l2rtspserver >/dev/null 2>&1; then
		install_camera_daemon_from_source
	else
		echo "v4l2rtspserver already available in PATH; skipping source build."
	fi
	echo
fi

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
python3 -c "import yaml; print('  pyyaml ✓')" 2>/dev/null || { echo "  pyyaml ✗"; FAILED=1; }

echo
if [[ $FAILED -eq 1 ]]; then
	echo "⚠  Some dependencies failed to install. Check the output above."
else
	echo "All dependencies installed successfully."
fi

if [[ $CAMERA_DAEMON -eq 1 ]]; then
	if command -v v4l2rtspserver >/dev/null 2>&1; then
		CAMERA_DAEMON_BIN_AVAILABLE=1
	fi

	echo
	echo "Camera daemon diagnostics:"
	echo "  RTSP URL default: rtsp://127.0.0.1:8554/unicast"
	if [[ $CAMERA_DAEMON_BIN_AVAILABLE -eq 1 ]]; then
		echo "  v4l2rtspserver binary: found ✓"
	else
		echo "  v4l2rtspserver binary: not found"
		echo "  Install from apt (if available) or use --build-camera-daemon-from-source"
	fi

	if CAMERA_DAEMON_SERVICE="$(detect_camera_daemon_service)"; then
		echo "  Detected service unit: ${CAMERA_DAEMON_SERVICE}.service"
	else
		echo "  No daemon service unit detected; local service can be created with --with-camera-daemon-autostart"
	fi

	if [[ $CAMERA_DAEMON_AUTOSTART -eq 1 ]]; then
		if [[ $CAMERA_DAEMON_BIN_AVAILABLE -ne 1 ]]; then
			echo "Cannot enable daemon autostart: v4l2rtspserver binary is missing."
			echo "Try: bash install.sh --with-camera-daemon --build-camera-daemon-from-source"
		elif [[ -z "$CAMERA_DAEMON_SERVICE" ]]; then
			echo "No packaged daemon service found; creating local service unit..."
			install_local_v4l2rtspserver_service
		fi

		if [[ -n "$CAMERA_DAEMON_SERVICE" ]]; then
			echo "Enabling ${CAMERA_DAEMON_SERVICE} autostart..."
			sudo systemctl enable --now "${CAMERA_DAEMON_SERVICE}" || true
			if sudo systemctl is-active --quiet "${CAMERA_DAEMON_SERVICE}"; then
				echo "  ${CAMERA_DAEMON_SERVICE} is active ✓"
			else
				echo "  ${CAMERA_DAEMON_SERVICE} is not active"
				echo "  Check: sudo systemctl status ${CAMERA_DAEMON_SERVICE}"
			fi
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
		echo "[4/4] Setting up desktop shortcut + app autostart..."
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
echo "  ./launch_dsi_touch.sh"
echo
if [[ $AUTOSTART -eq 0 ]]; then
	echo "App autostart is disabled by default."
	echo "To enable it later:"
	echo "  bash install.sh --autostart"
	echo
fi
echo "Notes for DSI displays:"
echo "  • No SPI LCD driver script is required for Freenove DSI displays"
echo "  • Ensure Raspberry Pi OS Desktop is running on the DSI panel"
if [[ $CAMERA_DAEMON -eq 1 ]]; then
	if [[ $CAMERA_DAEMON_BIN_AVAILABLE -eq 1 ]]; then
		echo "  • Camera daemon available (v4l2rtspserver + v4l-utils)"
	else
		echo "  • Camera tools installed (v4l-utils); daemon binary unavailable unless built/installed"
	fi
fi
echo
echo "A reboot is recommended after first install or daemon/autostart changes:"
echo "  sudo reboot"
echo "========================================="

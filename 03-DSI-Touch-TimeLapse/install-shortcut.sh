#!/usr/bin/env bash
set -euo pipefail

# Creates a desktop shortcut and optional autostart entry for Scenario 03
# (DSI Touch TimeLapse).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
AUTOSTART=0

while [[ $# -gt 0 ]]; do
	case "$1" in
		--autostart)
			AUTOSTART=1
			shift
			;;
		-h|--help)
			echo "Usage: ./install-shortcut.sh [--autostart]"
			exit 0
			;;
		*)
			echo "Unknown option: $1" >&2
			exit 1
			;;
	esac
done

DESKTOP_DIR="$HOME/Desktop"
AUTOSTART_DIR="$HOME/.config/autostart"
LAUNCHER_SCRIPT="$SCRIPT_DIR/launch_dsi_touch.sh"
DESKTOP_FILE="$DESKTOP_DIR/pitimelapse-dsi-touch.desktop"
AUTOSTART_FILE="$AUTOSTART_DIR/pitimelapse-dsi-touch.desktop"
LEGACY_DESKTOP_FILE="$DESKTOP_DIR/pitimelapse-dsi-touch-sudo.desktop"
LEGACY_AUTOSTART_FILE="$AUTOSTART_DIR/pitimelapse-dsi-touch-sudo.desktop"
USER_NAME="${SUDO_USER:-${USER:-pi}}"
USER_HOME=$(getent passwd "$USER_NAME" | cut -d: -f6)
if [[ -z "$USER_HOME" ]]; then
	USER_HOME="$HOME"
fi
XAUTHORITY_PATH="$USER_HOME/.Xauthority"

mkdir -p "$DESKTOP_DIR"
mkdir -p "$AUTOSTART_DIR"

cat > "$LAUNCHER_SCRIPT" << EOF
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"
export DISPLAY="\${DISPLAY:-:0}"
export XAUTHORITY="\${XAUTHORITY:-$XAUTHORITY_PATH}"

APP_PY="\${SCRIPT_DIR}/timelapse_touch.py"

python_candidates=(
	"\${SCRIPT_DIR}/.venv/bin/python3"
	"\${SCRIPT_DIR}/.venv/bin/python"
	"/usr/local/bin/python3"
	"/usr/bin/python3"
	"python3"
)

has_required_modules() {
	local py="\$1"
	"\$py" -c "import cv2, psutil" >/dev/null 2>&1
}

choose_python() {
	local py
	for py in "\${python_candidates[@]}"; do
		if [[ "\$py" == */* && ! -x "\$py" ]]; then
			continue
		fi
		if ! command -v "\$py" >/dev/null 2>&1; then
			continue
		fi
		if has_required_modules "\$py"; then
			echo "\$py"
			return 0
		fi
	done

	echo "/usr/bin/python3"
	return 0
}

PYTHON_BIN="\$(choose_python)"

if ! has_required_modules "\$PYTHON_BIN"; then
	echo "Warning: Selected Python (\${PYTHON_BIN}) is missing cv2 and/or psutil." >&2
	echo "The app may fail to detect camera/storage until dependencies are installed for this environment." >&2
fi

if [[ "\${EUID:-\$(id -u)}" == "0" ]]; then
	exec "\$PYTHON_BIN" "\$APP_PY" --fullscreen
fi

if sudo -n true >/dev/null 2>&1; then
	if sudo -n "\$PYTHON_BIN" -c "import cv2, psutil" >/dev/null 2>&1; then
		exec sudo -n --preserve-env=DISPLAY,XAUTHORITY "\$PYTHON_BIN" "\$APP_PY" --fullscreen
	fi

	USER_SITE="\$(\$PYTHON_BIN -c 'import site; print(site.getusersitepackages())' 2>/dev/null || true)"
	if [[ -n "\$USER_SITE" ]]; then
		export PYTHONPATH="\${USER_SITE}\${PYTHONPATH:+:\${PYTHONPATH}}"
		if sudo -n --preserve-env=PYTHONPATH "\$PYTHON_BIN" -c "import cv2, psutil" >/dev/null 2>&1; then
			exec sudo -n --preserve-env=DISPLAY,XAUTHORITY,PYTHONPATH "\$PYTHON_BIN" "\$APP_PY" --fullscreen
		fi
	fi
fi

echo "Warning: passwordless sudo is not configured for this user." >&2
echo "Launching without elevation; Grove relay GPIO access may be unavailable for one or more relays." >&2
exec "\$PYTHON_BIN" "\$APP_PY" --fullscreen
EOF

chmod 755 "$LAUNCHER_SCRIPT"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=PiTimeLapse DSI Touch
Comment=Time-lapse capture app for DSI screens with smart elevation support
Exec=${LAUNCHER_SCRIPT}
Path=${SCRIPT_DIR}
Icon=camera-photo
Terminal=true
Type=Application
Categories=Photography;
EOF

chmod 644 "$DESKTOP_FILE"

if [[ $AUTOSTART -eq 1 ]]; then
	cp "$DESKTOP_FILE" "$AUTOSTART_FILE"
	chmod 644 "$AUTOSTART_FILE"
else
	rm -f "$AUTOSTART_FILE"
fi

rm -f "$LEGACY_DESKTOP_FILE" "$LEGACY_AUTOSTART_FILE"

echo "✅ Desktop shortcut created: $DESKTOP_FILE"
echo "✅ Launcher script created: $LAUNCHER_SCRIPT"
if [[ $AUTOSTART -eq 1 ]]; then
	echo "✅ Autostart entry created: $AUTOSTART_FILE"
else
	echo "✅ Autostart entry removed (startup launch disabled by default)"
fi
echo ""
echo "You can now:"
echo "  • Double-tap the 'PiTimeLapse DSI Touch' icon on your desktop"
echo "  • Or run:  ${LAUNCHER_SCRIPT}"
echo ""
echo "Launcher behavior:"
echo "  • Uses the current root shell directly when already elevated"
echo "  • Uses passwordless sudo automatically when available"
echo "  • Falls back to a normal user launch with a warning if elevation is unavailable"

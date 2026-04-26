#!/usr/bin/env bash
set -euo pipefail

# Creates a desktop shortcut and optional autostart entry for Scenario 03
# (DSI Touch TimeLapse).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_FILE_SUDO="$HOME/Desktop/pitimelapse-dsi-touch-sudo.desktop"

# Note: Only the sudo launcher is created. The Grove WS281x LED requires /dev/mem access,
# which is only available with elevated permissions. Using a non-sudo launcher would silently
# fail with "Grove LED not detected" without providing clear feedback to the user.

cat > "$DESKTOP_FILE_SUDO" << EOF
[Desktop Entry]
Name=PiTimeLapse DSI Touch (sudo)
Comment=Time-lapse capture app with elevated permissions for Grove WS281x LED
Exec=/bin/bash -lc "export DISPLAY=:0; export XAUTHORITY=/home/pi/.Xauthority; exec sudo --preserve-env=DISPLAY,XAUTHORITY /usr/bin/python3 ${SCRIPT_DIR}/timelapse_touch.py --fullscreen"
Path=${SCRIPT_DIR}
Icon=camera-photo
Terminal=true
Type=Application
Categories=Photography;
EOF

chmod 644 "$DESKTOP_FILE_SUDO"
echo "✅ Desktop shortcut created: $DESKTOP_FILE_SUDO"
echo ""
echo "You can now:"
echo "  • Double-tap the 'PiTimeLapse DSI Touch (sudo)' icon on your desktop"
echo "  • Or run:  sudo python3 ${SCRIPT_DIR}/timelapse_touch.py --fullscreen"
echo ""
echo "Note: This app requires sudo for Grove WS281x LED access (/dev/mem permission required)."

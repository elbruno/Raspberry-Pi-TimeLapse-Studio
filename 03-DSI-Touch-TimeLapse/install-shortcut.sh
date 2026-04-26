#!/usr/bin/env bash
set -euo pipefail

# Creates a desktop shortcut and optional autostart entry for Scenario 03
# (DSI Touch TimeLapse).

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_FILE="$HOME/Desktop/pitimelapse-dsi-touch.desktop"
DESKTOP_FILE_SUDO="$HOME/Desktop/pitimelapse-dsi-touch-sudo.desktop"
AUTOSTART_DIR="$HOME/.config/autostart"
POLKIT_MATE_SYSTEM_FILE="/etc/xdg/autostart/polkit-mate-authentication-agent-1.desktop"
POLKIT_MATE_USER_OVERRIDE="$AUTOSTART_DIR/polkit-mate-authentication-agent-1.desktop"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=PiTimeLapse DSI Touch
Comment=Time-lapse capture app for Raspberry Pi DSI touchscreen
Exec=python3 ${SCRIPT_DIR}/timelapse_touch.py --fullscreen
Path=${SCRIPT_DIR}
Icon=camera-photo
Terminal=false
Type=Application
Categories=Photography;
EOF

chmod 644 "$DESKTOP_FILE"
echo "✅ Desktop shortcut created: $DESKTOP_FILE"

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
echo "✅ Elevated desktop shortcut created: $DESKTOP_FILE_SUDO"

if [ "${1:-}" = "--autostart" ]; then
    mkdir -p "$AUTOSTART_DIR"
    cp "$DESKTOP_FILE" "$AUTOSTART_DIR/pitimelapse-dsi-touch.desktop"
    chmod 644 "$AUTOSTART_DIR/pitimelapse-dsi-touch.desktop"

    if [ -f "$POLKIT_MATE_SYSTEM_FILE" ]; then
        cp "$POLKIT_MATE_SYSTEM_FILE" "$POLKIT_MATE_USER_OVERRIDE"
        if ! grep -q '^Hidden=true$' "$POLKIT_MATE_USER_OVERRIDE"; then
            printf '\nHidden=true\n' >> "$POLKIT_MATE_USER_OVERRIDE"
        fi
        chmod 644 "$POLKIT_MATE_USER_OVERRIDE"
        echo "✅ Disabled duplicate MATE PolicyKit autostart for this LXDE session"
    fi

    echo "✅ Autostart enabled — app will launch on boot"
    echo "   (Autostart uses the standard non-sudo launcher.)"
fi

echo ""
echo "You can now:"
echo "  • Double-tap the 'PiTimeLapse DSI Touch' icon on your desktop"
echo "  • Use 'PiTimeLapse DSI Touch (sudo)' when Grove WS281x LED needs elevated access"
echo "  • Or run:  python3 ${SCRIPT_DIR}/timelapse_touch.py --fullscreen"

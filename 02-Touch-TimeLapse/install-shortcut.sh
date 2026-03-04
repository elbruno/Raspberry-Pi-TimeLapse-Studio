#!/bin/bash
# Creates a desktop shortcut and optional autostart entry for PiTimeLapse Touch.
# Run once after cloning the repo on your Raspberry Pi.
#
# Usage:
#   chmod +x install-shortcut.sh
#   ./install-shortcut.sh              # desktop shortcut only
#   ./install-shortcut.sh --autostart  # also launch on boot

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_FILE="$HOME/Desktop/pitimelapse-touch.desktop"
AUTOSTART_DIR="$HOME/.config/autostart"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=PiTimeLapse Touch
Comment=Time-lapse capture app for Raspberry Pi touchscreen
Exec=python3 ${SCRIPT_DIR}/timelapse_touch.py --fullscreen
Path=${SCRIPT_DIR}
Icon=camera-photo
Terminal=false
Type=Application
Categories=Photography;
EOF

chmod +x "$DESKTOP_FILE"
echo "✅ Desktop shortcut created: $DESKTOP_FILE"

if [ "$1" = "--autostart" ]; then
    mkdir -p "$AUTOSTART_DIR"
    cp "$DESKTOP_FILE" "$AUTOSTART_DIR/pitimelapse-touch.desktop"
    echo "✅ Autostart enabled — app will launch on boot"
fi

echo ""
echo "You can now:"
echo "  • Double-tap the 'PiTimeLapse Touch' icon on your desktop"
echo "  • Or run:  python3 ${SCRIPT_DIR}/timelapse_touch.py --fullscreen"

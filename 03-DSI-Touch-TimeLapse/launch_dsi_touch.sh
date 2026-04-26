#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/pi/.Xauthority}"

if [[ "${EUID:-$(id -u)}" == "0" ]]; then
	exec /usr/bin/python3 "${SCRIPT_DIR}/timelapse_touch.py" --fullscreen
fi

if sudo -n true >/dev/null 2>&1; then
	exec sudo -n --preserve-env=DISPLAY,XAUTHORITY /usr/bin/python3 "${SCRIPT_DIR}/timelapse_touch.py" --fullscreen
fi

echo "Warning: passwordless sudo is not configured for this user." >&2
echo "Launching without elevation; Grove WS281x LED access may be unavailable." >&2
exec /usr/bin/python3 "${SCRIPT_DIR}/timelapse_touch.py" --fullscreen

#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/pi/.Xauthority}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"

# Expose the invoking user's pip --user packages (e.g. opencv-python) when
# the app is launched via sudo. Without this, root's Python cannot import
# cv2 and the camera silently fails to detect.
USER_SITE="/home/${SUDO_USER:-${USER:-pi}}/.local/lib/python3.13/site-packages"
if [[ "${EUID:-$(id -u)}" != "0" ]]; then
        # Capture pi user's site-packages before potentially elevating
        USER_SITE="/home/$(id -un)/.local/lib/python3.13/site-packages"
fi
export PYTHONPATH="${USER_SITE}${PYTHONPATH:+:${PYTHONPATH}}"

if [[ "${EUID:-$(id -u)}" == "0" ]]; then
        exec /usr/bin/python3 "${SCRIPT_DIR}/timelapse_touch.py" --fullscreen
fi

# Forward env vars root needs (display + cv2 site-packages + runtime dir)
PRESERVE_VARS="DISPLAY,XAUTHORITY,XDG_RUNTIME_DIR,PYTHONPATH"

if sudo -n true >/dev/null 2>&1; then
        exec sudo -n --preserve-env="${PRESERVE_VARS}" /usr/bin/python3 "${SCRIPT_DIR}/timelapse_touch.py" --fullscreen

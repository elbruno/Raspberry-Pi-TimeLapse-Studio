#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/pi/.Xauthority}"

APP_PY="${SCRIPT_DIR}/timelapse_touch.py"

python_candidates=(
	"${SCRIPT_DIR}/.venv/bin/python3"
	"${SCRIPT_DIR}/.venv/bin/python"
	"/usr/local/bin/python3"
	"/usr/bin/python3"
	"python3"
)

has_required_modules() {
	local py="$1"
	"$py" -c "import cv2, psutil" >/dev/null 2>&1
}

choose_python() {
	local py
	for py in "${python_candidates[@]}"; do
		if [[ "$py" == */* && ! -x "$py" ]]; then
			continue
		fi
		if ! command -v "$py" >/dev/null 2>&1; then
			continue
		fi
		if has_required_modules "$py"; then
			echo "$py"
			return 0
		fi
	done

	# Fallback to system python even if deps are missing; app will emit guidance.
	echo "/usr/bin/python3"
	return 0
}

PYTHON_BIN="$(choose_python)"

if ! has_required_modules "$PYTHON_BIN"; then
	echo "Warning: Selected Python (${PYTHON_BIN}) is missing cv2 and/or psutil." >&2
	echo "The app may fail to detect camera/storage until dependencies are installed for this environment." >&2
fi

if [[ "${EUID:-$(id -u)}" == "0" ]]; then
	exec "$PYTHON_BIN" "$APP_PY" --fullscreen
fi

if sudo -n true >/dev/null 2>&1; then
	if sudo -n "$PYTHON_BIN" -c "import cv2, psutil" >/dev/null 2>&1; then
		exec sudo -n --preserve-env=DISPLAY,XAUTHORITY "$PYTHON_BIN" "$APP_PY" --fullscreen
	fi

	# Root environment may not include user-installed packages. Borrow user site-packages.
	USER_SITE="$($PYTHON_BIN -c 'import site; print(site.getusersitepackages())' 2>/dev/null || true)"
	if [[ -n "$USER_SITE" ]]; then
		export PYTHONPATH="${USER_SITE}${PYTHONPATH:+:${PYTHONPATH}}"
		if sudo -n --preserve-env=PYTHONPATH "$PYTHON_BIN" -c "import cv2, psutil" >/dev/null 2>&1; then
			exec sudo -n --preserve-env=DISPLAY,XAUTHORITY,PYTHONPATH "$PYTHON_BIN" "$APP_PY" --fullscreen
		fi
	fi
fi

echo "Warning: passwordless sudo is not configured for this user." >&2
echo "Launching without elevation; Grove relay GPIO access may be unavailable for one or more relays." >&2
exec "$PYTHON_BIN" "$APP_PY" --fullscreen

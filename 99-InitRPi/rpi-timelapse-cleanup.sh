#!/usr/bin/env bash
set -euo pipefail

PROFILE="web"
APPLY=0
ASSUME_YES=0
SKIP_ANALYZE=0

usage() {
  cat <<'USAGE'
Raspberry Pi TimeLapse Studio cleanup helper

Usage:
  ./rpi-timelapse-cleanup.sh [--profile web|touch] [--apply] [--yes] [--skip-analyze]

Profiles:
  web    Keeps a headless / VS Code / SSH friendly setup for 01-WebApp-TimeLapse.
  touch  Keeps the desktop/X11 stack for 02-Touch-TimeLapse with LCD/touchscreen.

Behavior:
  - Default mode is DRY RUN. It only shows what would be removed.
  - Use --apply to actually purge packages.
  - Use --yes to skip the confirmation prompt.

Examples:
  bash rpi-timelapse-cleanup.sh --profile web
  bash rpi-timelapse-cleanup.sh --profile web --apply
  bash rpi-timelapse-cleanup.sh --profile touch --apply --yes
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)
      PROFILE="${2:-}"
      shift 2
      ;;
    --apply)
      APPLY=1
      shift
      ;;
    --yes)
      ASSUME_YES=1
      shift
      ;;
    --skip-analyze)
      SKIP_ANALYZE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$PROFILE" != "web" && "$PROFILE" != "touch" ]]; then
  echo "Invalid profile '$PROFILE'. Use 'web' or 'touch'." >&2
  exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
  echo "This script requires apt/apt-get (Raspberry Pi OS / Debian-based)." >&2
  exit 1
fi

echo "== Raspberry Pi TimeLapse Studio cleanup =="
echo "Profile : $PROFILE"
echo "Mode    : $([[ $APPLY -eq 1 ]] && echo APPLY || echo DRY RUN)"
echo

# Capture disk usage before cleanup for comparison
DISK_BEFORE=$(df / --output=used | tail -1 | tr -d ' ')

if [[ $SKIP_ANALYZE -eq 0 ]]; then
  echo "[1/7] Disk usage snapshot"
  df -h /
  echo

  echo "[2/7] Largest top-level directories under /"
  sudo du -xhd1 / 2>/dev/null | sort -h | tail -n 20 || true
  echo

  echo "[3/7] Largest top-level directories under /home"
  sudo du -xhd1 /home 2>/dev/null | sort -h | tail -n 20 || true
  echo

  echo "[4/7] Apt cache size"
  sudo du -sh /var/cache/apt/archives 2>/dev/null || true
  echo

  echo "[5/7] Journal disk usage"
  sudo journalctl --disk-usage || true
  echo

  echo "[6/7] Installed desktop/browser/editor/media package snapshot"
  dpkg-query -W -f='${Package}\n' \
    chromium* firefox* libreoffice* vlc* sonic-pi* scratch* wolfram* minecraft-pi* \
    geany* greenfoot* claws-mail* nuscratch* realvnc-vnc-viewer* thonny* \
    2>/dev/null | sort -u || true
  echo

  echo "[7/7] Reclaimable filesystem areas"
  echo "  Locales : $(sudo du -sh /usr/share/locale 2>/dev/null | cut -f1 || echo '?')"
  echo "  Docs    : $(sudo du -sh /usr/share/doc 2>/dev/null | cut -f1 || echo '?')"
  echo "  Man     : $(sudo du -sh /usr/share/man 2>/dev/null | cut -f1 || echo '?')"
  echo "  Apt list: $(sudo du -sh /var/lib/apt/lists 2>/dev/null | cut -f1 || echo '?')"
  echo "  Old logs: $(sudo find /var/log -name '*.gz' -o -name '*.1' -o -name '*.old' 2>/dev/null | xargs du -ch 2>/dev/null | tail -1 | cut -f1 || echo '?')"
  echo
fi

# Packages required or commonly useful for the repo/runtime
KEEP_BASE=(
  python3 python3-pip python3-venv python3-dev
  python3-picamera2
  ffmpeg
  libcamera0 libcamera-tools rpicam-apps
  git curl wget ca-certificates
  openssh-client openssh-server
  build-essential pkg-config
  rsync unzip zip tar gzip
)

# Extra packages worth keeping for touchscreen profile
KEEP_TOUCH=(
  xserver-xorg x11-xserver-utils xinit openbox lightdm
  python3-pygame python3-numpy python3-opencv
)

# Conservative removal candidates: large packages that are typically unnecessary
# for a dedicated timelapse Pi. Each removal is conditional on being installed.
COMMON_REMOVE=(
  libreoffice-common libreoffice-core libreoffice-base-core libreoffice-calc libreoffice-draw libreoffice-impress libreoffice-math libreoffice-writer
  chromium-browser chromium
  wolfram-engine wolframscript
  sonic-pi
  minecraft-pi
  scratch scratch2 nuscratch
  greenfoot
  claws-mail
  geany geany-common
  realvnc-vnc-viewer
  smartsim
  thonny thonny-py-helper   # Thonny IDE — not needed for headless/SSH dev
  vlc vlc-data vlc-plugin-base vlc-bin vlc-l10n  # media player
  cups cups-daemon cups-common  # printing support
)

# Additional packages to remove only in headless web profile.
# These intentionally target the desktop stack.
WEB_ONLY_REMOVE=(
  raspberrypi-ui-mods lxappearance lxde lxde-core lxde-common lxinput lxmenu-data lxpanel lxpolkit lxrandr lxsession lxsession-data lxterminal openbox lightdm pi-greeter
  xserver-common xserver-xorg x11-common x11-utils x11-xserver-utils xinit
  xserver-xorg-video-fbdev
  desktop-base raspberrypi-desktop pixflat-icons usb-modeswitch
)

# Touch profile avoids removing desktop/X11 because the touchscreen app relies on it.
TOUCH_ONLY_REMOVE=(
)

REMOVALS=("${COMMON_REMOVE[@]}")
if [[ "$PROFILE" == "web" ]]; then
  REMOVALS+=("${WEB_ONLY_REMOVE[@]}")
else
  REMOVALS+=("${TOUCH_ONLY_REMOVE[@]}")
fi

INSTALLED_TO_REMOVE=()
for pkg in "${REMOVALS[@]}"; do
  if dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null | grep -q "install ok installed"; then
    INSTALLED_TO_REMOVE+=("$pkg")
  fi
done

# Deduplicate package list
if [[ ${#INSTALLED_TO_REMOVE[@]} -gt 0 ]]; then
  mapfile -t INSTALLED_TO_REMOVE < <(printf '%s\n' "${INSTALLED_TO_REMOVE[@]}" | sort -u)
fi

echo "Packages we will KEEP for repo/runtime reference:"
printf '  - %s\n' "${KEEP_BASE[@]}"
if [[ "$PROFILE" == "touch" ]]; then
  printf '  - %s\n' "${KEEP_TOUCH[@]}"
fi

echo
if [[ ${#INSTALLED_TO_REMOVE[@]} -eq 0 ]]; then
  echo "No matching cleanup candidates are currently installed."
else
  echo "Packages selected for purge (${#INSTALLED_TO_REMOVE[@]}):"
  printf '  - %s\n' "${INSTALLED_TO_REMOVE[@]}"
fi

echo
if [[ $APPLY -eq 0 ]]; then
  echo "Dry run only. Nothing has been removed."
  echo
  echo "Next step to apply:"
  echo "  sudo bash $0 --profile $PROFILE --apply"
  exit 0
fi

if [[ ${#INSTALLED_TO_REMOVE[@]} -eq 0 ]]; then
  echo "Nothing to purge. Running cache/log cleanup only."
else
  if [[ $ASSUME_YES -eq 0 ]]; then
    read -r -p "Proceed with purge for profile '$PROFILE'? [y/N] " reply
    if [[ ! "$reply" =~ ^[Yy]$ ]]; then
      echo "Cancelled."
      exit 1
    fi
  fi

  echo
  echo "Purging selected packages..."
  sudo apt-get purge -y "${INSTALLED_TO_REMOVE[@]}"
fi

echo
# Housekeeping cleanup regardless of whether purge list was empty
echo "Running autoremove/autoclean/clean..."
sudo apt-get autoremove -y --purge
sudo apt-get autoclean -y
sudo apt-get clean

echo
# Trim logs conservatively
echo "Vacuuming journal logs to 7 days..."
sudo journalctl --vacuum-time=7d || true

echo
# Remove rotated/compressed log files
echo "Removing old rotated log files..."
sudo find /var/log -name '*.gz' -delete 2>/dev/null || true
sudo find /var/log -name '*.1' -delete 2>/dev/null || true
sudo find /var/log -name '*.old' -delete 2>/dev/null || true

echo
# Strip unused locales (keep English only). Saves 100-200 MB.
echo "Removing non-English locale data..."
sudo find /usr/share/locale -maxdepth 1 -mindepth 1 -type d \
  ! -name 'en' ! -name 'en_US' ! -name 'en_GB' -exec rm -rf {} + 2>/dev/null || true

echo
# Remove package documentation (keep copyright files for license compliance)
echo "Removing package docs (preserving copyright files)..."
sudo find /usr/share/doc -mindepth 2 ! -name 'copyright' -delete 2>/dev/null || true
sudo find /usr/share/doc -mindepth 1 -type d -empty -delete 2>/dev/null || true

echo
# Remove non-English man pages
echo "Removing non-English man pages..."
sudo find /usr/share/man -maxdepth 1 -mindepth 1 -type d \
  ! -name 'man*' -exec rm -rf {} + 2>/dev/null || true

echo
# Clear apt package lists (re-fetched automatically on next apt update)
echo "Clearing apt package lists..."
sudo rm -rf /var/lib/apt/lists/*

echo
# Clear user and root caches
echo "Clearing user caches..."
rm -rf "$HOME/.cache/pip" "$HOME/.cache/thumbnails" 2>/dev/null || true
sudo rm -rf /root/.cache/pip 2>/dev/null || true

echo
# Remove Python bytecode caches system-wide
echo "Removing stale Python __pycache__ dirs..."
sudo find /usr -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

echo
# Optional VS Code server cleanup to reclaim space / fix failed installs
# WARNING: This will disconnect an active VS Code Remote SSH session.
# Reconnecting after the script finishes will re-download the server.
echo "Cleaning old VS Code server caches from user home..."
rm -rf "$HOME/.vscode-server" "$HOME/.vscode-server-insiders" || true

echo
# Final report with before/after comparison
DISK_AFTER=$(df / --output=used | tail -1 | tr -d ' ')
SAVED_KB=$(( DISK_BEFORE - DISK_AFTER ))
SAVED_MB=$(( SAVED_KB / 1024 ))

echo "========================================="
echo "Final disk usage:"
df -h /
echo
if [[ $SAVED_MB -gt 0 ]]; then
  echo "Space recovered: ~${SAVED_MB} MB"
else
  echo "Space recovered: < 1 MB (most targets were already absent)"
fi
echo "========================================="

echo
echo "NOTE: Run 'sudo apt update' before installing new packages"
echo "      (apt lists were cleared to save space)."
echo
cat <<EOF2
Done.

Suggested next commands for Raspberry-Pi-TimeLapse-Studio:

  # Web scenario
  cd ~/Raspberry-Pi-TimeLapse-Studio/01-WebApp-TimeLapse
  sudo apt update
  pip3 install -r requirements.txt --break-system-packages
  python3 main.py validate

  # Touch scenario
  cd ~/Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
  sudo apt update
  pip3 install -r requirements.txt --break-system-packages
  python3 timelapse_touch.py --fullscreen
EOF2

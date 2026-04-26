#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME=$(basename "$0")
TARGET_USER=""
DISABLE=0

SUDOERS_FILE="/etc/sudoers.d/90-pitimelapse-elevated-defaults"
AUTO_ROOT_PROFILE="/etc/profile.d/zz-pitimelapse-auto-root.sh"
PYTHONPATH_PROFILE="/etc/profile.d/zz-pitimelapse-user-site-packages.sh"

usage() {
  cat <<'USAGE'
Enable internal-device elevated defaults for Raspberry Pi TimeLapse Studio.

This helper is intentionally opinionated for dedicated/internal devices:
  - enables passwordless sudo for the target user
  - auto-escalates interactive shells to root on login/SSH
  - preserves access to the target user's ~/.local Python packages when root

Usage:
  sudo bash enable-device-elevation.sh [--user <username>]
  sudo bash enable-device-elevation.sh --disable

Options:
  --user <username>  User account to elevate by default. Defaults to SUDO_USER,
                     then logname, then 'pi'.
  --disable          Remove the elevated-defaults configuration files.
  -h, --help         Show this help.

Notes:
  - This is for trusted/internal devices only.
  - Create ~/.pitimelapse-disable-auto-root for the target user to opt out of
    automatic root shells temporarily.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --user)
      TARGET_USER="${2:-}"
      shift 2
      ;;
    --disable)
      DISABLE=1
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

if [[ ${EUID} -ne 0 ]]; then
  echo "${SCRIPT_NAME} must run as root." >&2
  exit 1
fi

resolve_target_user() {
  if [[ -n "$TARGET_USER" ]]; then
    printf '%s\n' "$TARGET_USER"
    return
  fi

  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    printf '%s\n' "$SUDO_USER"
    return
  fi

  if command -v logname >/dev/null 2>&1; then
    local login_name
    login_name=$(logname 2>/dev/null || true)
    if [[ -n "$login_name" && "$login_name" != "root" ]]; then
      printf '%s\n' "$login_name"
      return
    fi
  fi

  printf 'pi\n'
}

install_file() {
  local destination="$1"
  local mode="$2"
  local content="$3"
  local tmp
  tmp=$(mktemp)
  printf '%s' "$content" > "$tmp"
  install -m "$mode" "$tmp" "$destination"
  rm -f "$tmp"
}

if [[ $DISABLE -eq 1 ]]; then
  rm -f "$SUDOERS_FILE" "$AUTO_ROOT_PROFILE" "$PYTHONPATH_PROFILE"
  echo "Removed elevated-defaults configuration."
  exit 0
fi

TARGET_USER=$(resolve_target_user)

if ! id "$TARGET_USER" >/dev/null 2>&1; then
  echo "Target user '$TARGET_USER' does not exist." >&2
  exit 1
fi

SUDOERS_CONTENT=$(cat <<EOF
# Raspberry-Pi-TimeLapse-Studio internal-device defaults
Defaults:${TARGET_USER} !authenticate
Defaults:${TARGET_USER} env_keep += "PITIMELAPSE_AUTO_ROOT_DONE PITIMELAPSE_DISABLE_AUTO_ROOT PITIMELAPSE_OWNER PYTHONPATH"
${TARGET_USER} ALL=(ALL:ALL) NOPASSWD:ALL
EOF
)

AUTO_ROOT_CONTENT=$(cat <<'EOF'
# Added by Raspberry-Pi-TimeLapse-Studio for dedicated/internal devices.
if [[ -t 0 && -t 1 ]] \
  && [[ "${EUID:-$(id -u)}" != "0" ]] \
  && [[ -z "${PITIMELAPSE_AUTO_ROOT_DONE:-}" ]] \
  && [[ -z "${PITIMELAPSE_DISABLE_AUTO_ROOT:-}" ]] \
  && [[ ! -f "${HOME}/.pitimelapse-disable-auto-root" ]]; then
  export PITIMELAPSE_AUTO_ROOT_DONE=1
  export PITIMELAPSE_OWNER="${USER:-$(id -un)}"
  exec sudo -n -E -i
fi
EOF
)

PYTHONPATH_CONTENT=$(cat <<'EOF'
# Added by Raspberry-Pi-TimeLapse-Studio so root shells can still use the
# invoking user's ~/.local Python packages on dedicated/internal devices.
if [[ "$(id -u)" == "0" ]]; then
  _pitimelapse_owner="${SUDO_USER:-${PITIMELAPSE_OWNER:-}}"
  if [[ -n "${_pitimelapse_owner}" && "${_pitimelapse_owner}" != "root" ]]; then
    _pitimelapse_pyver="python$(python3 -c 'import sys; print("{}.{}".format(sys.version_info.major, sys.version_info.minor))')"
    _pitimelapse_site="/home/${_pitimelapse_owner}/.local/lib/${_pitimelapse_pyver}/site-packages"
    if [[ -d "${_pitimelapse_site}" ]]; then
      export PYTHONPATH="${_pitimelapse_site}${PYTHONPATH:+:${PYTHONPATH}}"
    fi
    unset _pitimelapse_pyver _pitimelapse_site
  fi
  unset _pitimelapse_owner
fi
EOF
)

install_file "$SUDOERS_FILE" 0440 "$SUDOERS_CONTENT"
if command -v visudo >/dev/null 2>&1; then
  visudo -cf "$SUDOERS_FILE"
fi

install_file "$AUTO_ROOT_PROFILE" 0644 "$AUTO_ROOT_CONTENT"
install_file "$PYTHONPATH_PROFILE" 0644 "$PYTHONPATH_CONTENT"

echo "Enabled elevated defaults for user: $TARGET_USER"
echo "  - passwordless sudo is active"
echo "  - interactive logins now auto-escalate to root"
echo "  - root shells can still see /home/$TARGET_USER/.local Python packages"
echo
echo "Opt-out for one user account:"
echo "  touch /home/$TARGET_USER/.pitimelapse-disable-auto-root"
echo
echo "Disable later:"
echo "  sudo bash $(realpath "$0") --disable"
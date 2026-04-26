#!/usr/bin/env bash
# -----------------------------------------------------------
# Scenario 03 cleanup helper (DSI Touch TimeLapse)
# -----------------------------------------------------------
# Wraps the repository-wide cleanup script with the correct
# profile for Scenario 03:
#   --profile touch  (keeps desktop/X11)
#
# Why this script exists:
# - Scenario 03 should keep Raspberry Pi OS Desktop/X11
# - Scenario 03 should remove unnecessary software and caches
# - Scenario 03 should NOT install SPI/GPIO LCD drivers
#
# Usage:
#   chmod +x cleanup.sh
#   ./cleanup.sh            # dry run (recommended first)
#   ./cleanup.sh --apply    # apply cleanup + apt update
#   ./cleanup.sh --apply --yes
# -----------------------------------------------------------
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_CLEANUP_SCRIPT="${SCRIPT_DIR}/../99-InitRPi/rpi-timelapse-cleanup.sh"
APPLY=0
ASSUME_YES=0
SKIP_ANALYZE=0

usage() {
  cat <<'USAGE'
Scenario 03 cleanup helper

Usage:
  ./cleanup.sh [--apply] [--yes] [--skip-analyze]

Options:
  --apply         Apply cleanup (default is dry run)
  --yes           Skip confirmation prompt when applying
  --skip-analyze  Skip optional package analysis section
  -h, --help      Show this help

Examples:
  ./cleanup.sh
  ./cleanup.sh --apply
  ./cleanup.sh --apply --yes
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "$REPO_CLEANUP_SCRIPT" ]]; then
  echo "Cleanup script not found: $REPO_CLEANUP_SCRIPT" >&2
  echo "Run this script from inside the repository clone." >&2
  exit 1
fi

CMD=(bash "$REPO_CLEANUP_SCRIPT" --profile touch)
if [[ $APPLY -eq 1 ]]; then
  CMD+=(--apply)
fi
if [[ $ASSUME_YES -eq 1 ]]; then
  CMD+=(--yes)
fi
if [[ $SKIP_ANALYZE -eq 1 ]]; then
  CMD+=(--skip-analyze)
fi

echo "== Scenario 03 Cleanup (DSI Touch) =="
echo "Command: ${CMD[*]}"
echo

if [[ $APPLY -eq 1 ]]; then
  sudo "${CMD[@]}"
  echo
  echo "Refreshing apt package lists..."
  sudo apt update
  echo "Cleanup complete."
else
  "${CMD[@]}"
fi

echo
cat <<'NOTE'
Note for Scenario 03:
  - This cleanup keeps desktop/X11 (touch profile).
  - Do not run SPI/GPIO LCD setup scripts for DSI screens.
NOTE

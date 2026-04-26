#!/usr/bin/env python3
"""
Scenario 03 — DSI Touch TimeLapse launcher.

This scenario reuses the full Scenario 02 application code and UI, but keeps
its own local config and install workflow tailored for DSI touch displays
(like the Freenove 7" DSI panel).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
SCENARIO_02_DIR = THIS_DIR.parent / "02-Touch-TimeLapse"

if not SCENARIO_02_DIR.exists():
    raise FileNotFoundError(
        f"Could not find Scenario 02 folder at: {SCENARIO_02_DIR}"
    )

# Ensure config.yaml and ./data are resolved from this Scenario 03 folder.
os.chdir(THIS_DIR)

# Import the real app entry point from Scenario 02.
sys.path.insert(0, str(SCENARIO_02_DIR))
from timelapse_touch import main as scenario_02_main  # type: ignore


if __name__ == "__main__":
    scenario_02_main()

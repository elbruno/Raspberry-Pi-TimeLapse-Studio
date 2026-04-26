#!/usr/bin/env python3
"""
test_led_usb_port.py - Quick test script for new USB port power LED controller

Usage:
    # Auto-detect mode
    sudo python test_led_usb_port.py
    
    # Explicit port
    sudo python test_led_usb_port.py --port 1-1.2

Note: Requires uhubctl installed and root permissions
      Install: sudo apt install uhubctl
"""

import argparse
import logging
import sys
import time

from led_controller import LEDController

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Test USB port power LED control")
    parser.add_argument(
        "--port",
        default="auto",
        help="USB port to control (e.g., '1-1.2') or 'auto' to detect"
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=3,
        help="Number of on/off cycles to perform"
    )
    args = parser.parse_args()

    logger.info("Testing USB LED Controller")
    logger.info("Port configuration: %s", args.port)
    logger.info("")

    # Create controller
    controller = LEDController(usb_port=args.port)

    # Detect
    logger.info("Detecting USB LED port...")
    if not controller.detect():
        logger.error("No controllable USB port found for LED")
        logger.error("")
        logger.error("Troubleshooting:")
        logger.error("  1. Install uhubctl: sudo apt install uhubctl")
        logger.error("  2. Run this script with sudo")
        logger.error("  3. Check that your USB hub supports per-port power switching")
        logger.error("  4. Run 'uhubctl' to list available ports")
        sys.exit(1)

    logger.info("✓ LED controller ready on port: %s", controller.port_name)
    logger.info("")

    try:
        # Perform test cycles
        for i in range(args.cycles):
            logger.info("Cycle %d/%d: Turning LED ON", i + 1, args.cycles)
            if not controller.turn_on():
                logger.error("Failed to turn LED on")
                break
            time.sleep(1.5)

            logger.info("Cycle %d/%d: Turning LED OFF", i + 1, args.cycles)
            if not controller.turn_off():
                logger.error("Failed to turn LED off")
                break
            time.sleep(1.0)

        logger.info("")
        logger.info("✓ Test completed successfully")

    finally:
        logger.info("Closing LED controller")
        controller.close()


if __name__ == "__main__":
    main()

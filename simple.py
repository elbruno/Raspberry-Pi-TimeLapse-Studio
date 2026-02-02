#!/usr/bin/env python3
"""
simple.py - A Minimal Time-Lapse Script for Beginners
======================================================

This is the simplest possible time-lapse script. It demonstrates the core
concepts with minimal code:

1. Open a camera
2. Take photos at regular intervals
3. Save them with timestamps
4. Stop with Ctrl+C

No web interface, no preview window - just the essentials!

Run it with:
    python simple.py

Stop it with:
    Ctrl+C

Requirements:
    pip install opencv-python-headless

Author: PiTimeLapse Lab Project
License: MIT
"""

# =============================================================================
# IMPORTS
# =============================================================================

import cv2                      # OpenCV - camera and image handling
import os                       # For creating folders
import time                     # For timing between captures
from datetime import datetime   # For timestamps in filenames


# =============================================================================
# CONFIGURATION - Change these values to customize behavior
# =============================================================================

INTERVAL_SECONDS = 10      # Time between photos
WIDTH = 640                # Image width in pixels
HEIGHT = 480               # Image height in pixels
OUTPUT_FOLDER = "simple_data"
JPEG_QUALITY = 85          # 0-100, higher = better quality


# =============================================================================
# MAIN SCRIPT
# =============================================================================

def main():
    """Main function - runs the time-lapse capture loop."""
    
    print("=" * 40)
    print("Simple Time-Lapse Script")
    print("=" * 40)
    print(f"Interval: {INTERVAL_SECONDS} seconds")
    print(f"Output: {OUTPUT_FOLDER}/")
    print("Press Ctrl+C to stop")
    print("=" * 40)
    print()
    
    # --- Step 1: Create output folder ---
    # os.makedirs creates the folder if it doesn't exist
    # exist_ok=True prevents errors if folder already exists
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"Output folder ready: {OUTPUT_FOLDER}")
    
    # --- Step 2: Open the camera ---
    # VideoCapture(0) opens the first available camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open camera!")
        return
    
    # Set the resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    print(f"Camera opened at {WIDTH}x{HEIGHT}")
    
    # Warm up: cameras need a moment to adjust exposure
    print("Warming up camera...")
    for _ in range(5):
        cap.read()
        time.sleep(0.1)
    
    # --- Step 3: Capture loop ---
    print()
    print("Starting captures...")
    photo_count = 0
    
    try:
        while True:
            # Capture a frame
            ret, frame = cap.read()
            
            if not ret:
                print("ERROR: Could not capture frame!")
                break
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            
            # Save the image
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            photo_count += 1
            print(f"[{photo_count}] Saved: {filename}")
            
            # Wait for next capture
            time.sleep(INTERVAL_SECONDS)
    
    except KeyboardInterrupt:
        # Ctrl+C was pressed
        print()
        print("Stopped by user")
    
    # --- Step 4: Cleanup ---
    cap.release()  # Release the camera
    
    print()
    print(f"Done! Captured {photo_count} photos")
    print(f"Photos saved in: {OUTPUT_FOLDER}/")


# =============================================================================
# ENTRY POINT
# =============================================================================

# This runs main() only when the script is executed directly
if __name__ == "__main__":
    main()

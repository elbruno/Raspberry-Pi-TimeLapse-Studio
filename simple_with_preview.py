#!/usr/bin/env python3
"""
simple_with_preview.py - Time-Lapse Script with Live Preview
=============================================================

This script extends simple.py by adding a live preview window. You can see
what the camera sees in real-time, with a countdown to the next capture.

What this script does:
1. Opens your camera
2. Shows a live preview window
3. Takes a photo every 10 seconds
4. Saves photos with timestamps
5. Stops when you press ESC or Ctrl+C

Run it with:
    python simple_with_preview.py

Stop it with:
    Press ESC in the preview window, or Ctrl+C in terminal

Requirements:
    pip install opencv-python  (NOT headless - needs GUI support)

Note: This requires a display. On headless systems (no monitor),
use simple.py instead.

Author: PiTimeLapse Lab Project
License: MIT
"""

# =============================================================================
# IMPORTS
# =============================================================================

import cv2                      # OpenCV - camera, image, and GUI handling
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
# HELPER FUNCTIONS
# =============================================================================

def draw_status_overlay(frame, photo_count, countdown):
    """
    Draw status information on the preview frame.
    
    Args:
        frame: The image to draw on (modified in place)
        photo_count: Number of photos taken so far
        countdown: Seconds until next capture
    """
    # Build status text
    text = f"Photos: {photo_count} | Next in: {countdown:.1f}s | ESC to quit"
    
    # Draw black background for better readability
    cv2.rectangle(frame, (5, 5), (450, 35), (0, 0, 0), -1)
    
    # Draw the text in green
    cv2.putText(
        frame,                      # Image to draw on
        text,                       # Text string
        (10, 28),                   # Position (x, y)
        cv2.FONT_HERSHEY_SIMPLEX,   # Font
        0.6,                        # Font scale
        (0, 255, 0),                # Color (BGR - green)
        2                           # Thickness
    )


# =============================================================================
# MAIN SCRIPT
# =============================================================================

def main():
    """Main function - runs the time-lapse capture loop with preview."""
    
    print("=" * 50)
    print("Time-Lapse Script with Live Preview")
    print("=" * 50)
    print(f"Interval: {INTERVAL_SECONDS} seconds")
    print(f"Output: {OUTPUT_FOLDER}/")
    print("Press ESC in preview window to stop")
    print("=" * 50)
    print()
    
    # --- Step 1: Create output folder ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"Output folder ready: {OUTPUT_FOLDER}")
    
    # --- Step 2: Open the camera ---
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open camera!")
        return
    
    # Set the resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera opened at {actual_w}x{actual_h}")
    
    # Warm up camera
    print("Warming up camera...")
    for _ in range(5):
        cap.read()
        time.sleep(0.1)
    
    # --- Step 3: Main loop with preview ---
    print()
    print("Starting capture loop...")
    print("(Press ESC in preview window to stop)")
    print()
    
    photo_count = 0
    last_capture_time = 0  # Force immediate first capture
    
    try:
        while True:
            current_time = time.time()
            
            # Read a frame for preview
            ret, frame = cap.read()
            if not ret or frame is None:
                print("ERROR: Could not read frame!")
                break
            
            # Calculate time since last capture
            time_since_capture = current_time - last_capture_time
            
            # Check if it's time to save a photo
            if time_since_capture >= INTERVAL_SECONDS:
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"photo_{timestamp}.jpg"
                filepath = os.path.join(OUTPUT_FOLDER, filename)
                
                # Save the image
                cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                photo_count += 1
                print(f"[{photo_count}] Saved: {filename}")
                
                last_capture_time = current_time
            
            # Calculate countdown for display
            countdown = max(0, INTERVAL_SECONDS - time_since_capture)
            
            # Draw status overlay on the frame
            draw_status_overlay(frame, photo_count, countdown)
            
            # Show the preview window
            cv2.imshow("Time-Lapse Preview (ESC to quit)", frame)
            
            # Check for ESC key (key code 27)
            # waitKey(1) waits 1ms and returns pressed key
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print()
                print("ESC pressed - stopping...")
                break
    
    except KeyboardInterrupt:
        print()
        print("Stopped by user (Ctrl+C)")
    
    except cv2.error as e:
        print()
        print(f"OpenCV error: {e}")
        print("Note: This script requires a display. Use simple.py for headless systems.")
    
    # --- Step 4: Cleanup ---
    cap.release()
    cv2.destroyAllWindows()
    
    print()
    print(f"Done! Captured {photo_count} photos")
    print(f"Photos saved in: {OUTPUT_FOLDER}/")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()

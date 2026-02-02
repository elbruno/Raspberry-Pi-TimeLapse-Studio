#!/usr/bin/env python3
"""
simple_with_preview.py - Time-Lapse Script with Live Preview
=============================================================

This script extends simple.py by adding a LIVE PREVIEW WINDOW! You can see
what the camera sees in real-time, with a countdown to the next capture.

🎓 WHAT'S DIFFERENT FROM simple.py?
    - Shows a live video preview window
    - Displays countdown timer and photo count on screen
    - Can be stopped with ESC key (more convenient than Ctrl+C)
    - Requires a monitor/display to work

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

Note: This requires a display. On headless systems (like a Raspberry Pi
accessed via SSH without a monitor), use simple.py instead.

💡 TRY THIS:
    1. Run this script and position your camera for a time-lapse
    2. Watch the countdown timer - photos are saved when it reaches 0
    3. Try covering and uncovering the camera - see the preview update!
    4. Press ESC to stop when you're done

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
# HELPER FUNCTIONS - Small reusable pieces of code
# =============================================================================

def draw_status_overlay(frame, photo_count, countdown):
    """
    Draw status information on the preview frame.
    
    🎓 HOW DRAWING WORKS IN OpenCV:
    OpenCV can draw shapes and text directly onto images. The image is modified
    "in place" - meaning we change the original, not a copy.
    
    Args:
        frame: The image to draw on (a 2D grid of pixels)
        photo_count: Number of photos taken so far
        countdown: Seconds until next capture
    """
    # Build the status text that will be shown on screen
    text = f"Photos: {photo_count} | Next in: {countdown:.1f}s | ESC to quit"
    
    # 🎓 UNDERSTANDING COORDINATES:
    # In computer graphics, (0,0) is the TOP-LEFT corner, not bottom-left!
    # X increases going RIGHT, Y increases going DOWN.
    # 
    # (0,0) ──────► X
    #   │
    #   │
    #   ▼
    #   Y
    
    # Draw a black rectangle as background for the text (so it's readable)
    # Parameters: image, top-left corner, bottom-right corner, color, fill
    # The -1 for the last parameter means "fill the rectangle"
    cv2.rectangle(
        frame,              # The image to draw on
        (5, 5),             # Top-left corner: 5 pixels from left, 5 from top
        (450, 35),          # Bottom-right: 450 pixels wide, 35 pixels tall
        (0, 0, 0),          # Color: (Blue, Green, Red) = pure black
        -1                  # Thickness: -1 means "fill it in"
    )
    
    # 🎓 BGR vs RGB:
    # OpenCV uses BGR (Blue-Green-Red) instead of RGB (Red-Green-Blue)!
    # This is a historical quirk from early camera hardware.
    # Common colors:
    #   (0, 0, 255)   = RED    (0 blue, 0 green, 255 red)
    #   (0, 255, 0)   = GREEN  (0 blue, 255 green, 0 red)
    #   (255, 0, 0)   = BLUE   (255 blue, 0 green, 0 red)
    #   (0, 255, 255) = YELLOW (green + red mixed)
    #   (255, 255, 255) = WHITE (all colors at max)
    
    # Draw the text in green
    cv2.putText(
        frame,                      # Image to draw on
        text,                       # The text string to display
        (10, 28),                   # Position: 10 pixels from left, 28 from top
                                    # (this is the BOTTOM-left of the text!)
        cv2.FONT_HERSHEY_SIMPLEX,   # Font style (there are several to choose from)
        0.6,                        # Font scale (size multiplier)
        (0, 255, 0),                # Color: bright green in BGR format
        2                           # Thickness: how bold the text is
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
        print()
        print("❌ ERROR: Could not open camera!")
        print()
        print("Common causes:")
        print("  • No camera connected")
        print("  • Camera in use by another program")
        print("  • On Raspberry Pi: camera not enabled")
        print()
        print("🔧 TRY: Close video apps and run again")
        return
    
    # Set the resolution and check what we actually got
    # (cameras don't always support every resolution!)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    
    # Get the ACTUAL resolution (might be different from what we asked for)
    actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"Camera opened at {actual_w}x{actual_h}")
    
    if actual_w != WIDTH or actual_h != HEIGHT:
        print(f"   (Note: requested {WIDTH}x{HEIGHT}, camera gave us {actual_w}x{actual_h})")
    
    # Warm up camera - let it adjust exposure and white balance
    print("Warming up camera...")
    for _ in range(5):
        cap.read()
        time.sleep(0.1)
    
    # --- Step 3: Main loop with preview ---
    # 
    # 🎓 KEY DIFFERENCE FROM simple.py:
    # In simple.py, we read a frame, save it, then sleep for the interval.
    # Here, we read frames CONSTANTLY (for smooth video preview) and only
    # SAVE when enough time has passed. This is more complex but gives us
    # a live video view!
    
    print()
    print("🎬 Starting capture loop with preview...")
    print("   (Press ESC in preview window to stop)")
    print()
    
    photo_count = 0
    last_capture_time = 0  # Setting to 0 forces an immediate first capture
    
    try:
        while True:
            # Get the current time (as seconds since 1970 - called "Unix time")
            current_time = time.time()
            
            # Read a frame for the live preview
            ret, frame = cap.read()
            if not ret or frame is None:
                print()
                print("❌ ERROR: Could not read frame!")
                print("   Camera may have been disconnected.")
                break
            
            # Calculate how long since we last saved a photo
            time_since_capture = current_time - last_capture_time
            
            # Is it time to save a photo?
            if time_since_capture >= INTERVAL_SECONDS:
                # Generate unique filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"photo_{timestamp}.jpg"
                filepath = os.path.join(OUTPUT_FOLDER, filename)
                
                # Save the image
                cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
                photo_count += 1
                print(f"📸 [{photo_count}] Saved: {filename}")
                
                # Remember when we captured this photo
                last_capture_time = current_time
            
            # Calculate countdown for the display overlay
            countdown = max(0, INTERVAL_SECONDS - time_since_capture)
            
            # Draw the status overlay on the frame
            draw_status_overlay(frame, photo_count, countdown)
            
            # 🎓 SHOWING THE PREVIEW WINDOW:
            # cv2.imshow() creates (or updates) a window with the given name.
            # The window stays open until we call cv2.destroyAllWindows().
            cv2.imshow("Time-Lapse Preview (ESC to quit)", frame)
            
            # 🎓 CHECKING FOR KEY PRESSES:
            # waitKey(1) does two things:
            #   1. Waits 1 millisecond (needed for the window to update)
            #   2. Returns the key code if a key was pressed
            # The "& 0xFF" is a trick to make it work on all systems.
            # ESC key has code 27.
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC key
                print()
                print("⏹️  ESC pressed - stopping...")
                break
    
    except KeyboardInterrupt:
        print()
        print("⏹️  Stopped by user (Ctrl+C)")
    
    except cv2.error as e:
        # This happens when OpenCV can't create a window (no display available)
        print()
        print(f"❌ OpenCV error: {e}")
        print()
        print("This usually means no display is available.")
        print("If you're connected via SSH, try one of these:")
        print("  1. Use simple.py instead (no preview window)")
        print("  2. Connect via SSH with X11 forwarding: ssh -X pi@hostname")
        print("  3. Connect directly to a monitor on the Pi")
    
    # --- Step 4: Cleanup ---
    cap.release()
    cv2.destroyAllWindows()  # Close all OpenCV windows
    
    # Show final summary
    print()
    print("=" * 50)
    print(f"✅ Done! Captured {photo_count} photos")
    print(f"📁 Photos saved in: {OUTPUT_FOLDER}/")
    print("=" * 50)
    print()
    print("💡 WHAT'S NEXT?")
    print("   • Try the full web app: python main.py")
    print("   • Make a video from your photos using FFmpeg")
    print("   • Experiment with different INTERVAL_SECONDS values")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    main()

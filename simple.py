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

🎓 LEARNING GOALS:
    - Understand how Python controls a camera
    - Learn about loops and timing
    - See how files are saved with timestamps
    - Practice starting and stopping programs

💡 TRY THIS:
    After running this script once, try these experiments:
    1. Change INTERVAL_SECONDS to 5 - What happens?
    2. Change WIDTH and HEIGHT to 1280 and 720 - Are photos bigger?
    3. Look in the simple_data folder - How are the files named?
    4. What happens if you unplug the camera while it's running?

Author: PiTimeLapse Lab Project
License: MIT
"""

# =============================================================================
# IMPORTS - These bring in code that other programmers wrote for us to use
# =============================================================================
# 
# Think of imports like borrowing tools from a toolbox. Instead of building
# everything from scratch, we use code that experts have already written!

import cv2                      # OpenCV - a powerful library for camera and image handling
                                # This gives us the ability to talk to cameras and save images

import os                       # "os" stands for Operating System
                                # This helps us work with folders and files on your computer

import time                     # Gives us tools to pause the program (like time.sleep)
                                # We use this to wait between taking photos

from datetime import datetime   # Helps us work with dates and times
                                # We use this to create unique filenames with timestamps


# =============================================================================
# CONFIGURATION - Change these values to customize your time-lapse!
# =============================================================================
# 
# These are called "constants" because they stay the same while the program runs.
# We write them in ALL_CAPS so it's easy to see they're special values.
#
# 💡 TRY CHANGING THESE VALUES and see what happens!

INTERVAL_SECONDS = 10      # How many seconds to wait between photos
                           # Try: 5 for faster capturing, 30 for slower

WIDTH = 640                # How wide each photo is (in pixels)
HEIGHT = 480               # How tall each photo is (in pixels)
                           # Try: 1280 x 720 for HD quality (bigger files!)

OUTPUT_FOLDER = "simple_data"  # The folder where photos will be saved
                               # This folder is created automatically

JPEG_QUALITY = 85          # How good the image quality is (0-100)
                           # Higher = better quality but bigger files
                           # Try: 95 for great quality, 50 for small files


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
    # 
    # 🎓 WHAT'S HAPPENING:
    # VideoCapture(0) tells the computer to connect to camera number 0.
    # Most computers only have one camera, so 0 is usually correct.
    # If you have multiple cameras, try 1 or 2 instead.
    #
    # 💡 TRY THIS: If you have a USB webcam, unplug it and run again.
    #             You'll see the error message below!
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        # The camera couldn't be opened - let's give helpful advice!
        print()
        print("❌ ERROR: Could not open camera!")
        print()
        print("This usually means one of these things:")
        print("  1. No camera is connected to your computer")
        print("  2. Another program (like Zoom or Teams) is using the camera")
        print("  3. On Raspberry Pi: the camera might not be enabled")
        print()
        print("🔧 TRY THESE FIXES:")
        print("  • Close any video chat apps and try again")
        print("  • Check that your camera is plugged in properly")
        print("  • On Raspberry Pi: run 'sudo raspi-config' to enable camera")
        print("  • Try: python -c \"import cv2; print(cv2.VideoCapture(0).isOpened())\"")
        return
    
    # Set the resolution (how big each photo will be)
    # cap.set() changes camera settings
    # CAP_PROP_FRAME_WIDTH and CAP_PROP_FRAME_HEIGHT are special codes OpenCV understands
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    print(f"Camera opened at {WIDTH}x{HEIGHT}")
    
    # 🎓 WHY WARM UP THE CAMERA?
    # When a camera first turns on, it needs a moment to adjust:
    #   - Auto-exposure: figuring out how bright the scene is
    #   - White balance: adjusting colors so white things look white
    # The first few frames are often too dark or have wrong colors!
    # By reading (and throwing away) a few frames, we let the camera adjust.
    #
    # 💡 TRY THIS: Comment out the warm-up loop below and see if your
    #             first photo looks darker or has strange colors!
    print("Warming up camera (letting it adjust to light)...")
    for _ in range(5):        # Read 5 frames and throw them away
        cap.read()            # Read a frame (we don't save it)
        time.sleep(0.1)       # Wait 0.1 seconds (100 milliseconds)
    
    # --- Step 3: Capture loop (the heart of time-lapse!) ---
    # 
    # 🎓 WHAT'S A LOOP?
    # A loop runs the same code over and over. "while True" means
    # "keep doing this forever" - or until we tell it to stop!
    # 
    # The loop will:
    #   1. Take a photo
    #   2. Save it with a unique filename
    #   3. Wait for the interval time
    #   4. Repeat!
    
    print()
    print("Starting captures... (Press Ctrl+C to stop)")
    print()
    photo_count = 0
    
    try:
        while True:
            # Capture a frame (a single image) from the camera
            # ret = True if successful, frame = the actual image data
            ret, frame = cap.read()
            
            if not ret:
                # Something went wrong with the camera
                print()
                print("❌ ERROR: Could not capture frame!")
                print()
                print("This can happen if:")
                print("  • The camera was unplugged while running")
                print("  • The USB cable is loose or damaged")
                print("  • The camera overheated (rare)")
                print()
                print("🔧 TRY: Unplug the camera, wait 5 seconds, plug it back in")
                break
            
            # 🎓 CREATE A UNIQUE FILENAME
            # We use the current date and time to make each filename unique.
            # strftime() formats the date/time as text:
            #   %Y = year (2024), %m = month (01-12), %d = day (01-31)
            #   %H = hour (00-23), %M = minute (00-59), %S = second (00-59)
            # This creates filenames like: photo_20240115_143052.jpg
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            
            # Save the image to a file
            # cv2.imwrite saves images - it figures out the format from the filename
            # The third parameter sets JPEG quality (0-100)
            cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            photo_count += 1
            print(f"📸 [{photo_count}] Saved: {filename}")
            
            # Wait for the next capture
            # time.sleep() pauses the program for the specified seconds
            time.sleep(INTERVAL_SECONDS)
    
    except KeyboardInterrupt:
        # 🎓 WHAT'S KeyboardInterrupt?
        # When you press Ctrl+C, Python raises a "KeyboardInterrupt" exception.
        # An exception is Python's way of saying "something unusual happened!"
        # By "catching" this exception with try/except, we can handle it
        # gracefully instead of the program crashing with an ugly error.
        print()
        print("⏹️  Stopped by user (you pressed Ctrl+C)")
    
    # --- Step 4: Cleanup (very important!) ---
    # 
    # 🎓 WHY RELEASE THE CAMERA?
    # The camera is a shared resource - only one program can use it at a time.
    # If we don't release it, other programs (or even this script run again!)
    # won't be able to access it until you restart your computer.
    # Always clean up after yourself!
    cap.release()
    
    # 🎉 Show the final summary
    print()
    print("=" * 40)
    print(f"✅ Done! Captured {photo_count} photos")
    print(f"📁 Photos saved in: {OUTPUT_FOLDER}/")
    print("=" * 40)
    print()
    print("💡 NEXT STEPS:")
    print("   • Open the folder and look at your photos")
    print("   • Try changing INTERVAL_SECONDS and running again")
    print("   • Ready for more? Try simple_with_preview.py")


# =============================================================================
# ENTRY POINT - Where the program begins
# =============================================================================
# 
# 🎓 WHAT DOES THIS DO?
# When you run "python simple.py", Python looks for this special check.
# __name__ is a built-in variable that Python sets automatically:
#   - If you RUN this file directly, __name__ is "__main__"
#   - If you IMPORT this file from another file, __name__ is "simple"
# 
# This pattern lets you use this file two ways:
#   1. Run it directly: python simple.py (runs main())
#   2. Import it: from simple import main (doesn't run automatically)

if __name__ == "__main__":
    main()

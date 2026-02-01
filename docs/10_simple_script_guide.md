# 📚 Simple Time-Lapse Scripts Guide

This guide covers two standalone learning scripts that teach time-lapse fundamentals:

| Script | Purpose | Requires Display? |
|--------|---------|-------------------|
| `simple.py` | Minimal code - best for learning | No |
| `simple_with_preview.py` | Adds live preview window | Yes |

**Start with `simple.py`** to understand the basics, then explore `simple_with_preview.py` to see how to add a GUI.

---

## 🎯 simple.py - The Minimal Script

This ~80-line script is the **simplest possible time-lapse implementation**. Perfect for understanding the core concepts.

### Quick Start

```bash
python simple.py     # Start capturing
# Press Ctrl+C to stop
```

### What It Does

1. Creates an output folder (`simple_data/`)
2. Opens the first available camera
3. Takes a photo every 10 seconds
4. Saves photos with timestamps like `photo_20260201_143052.jpg`
5. Stops when you press Ctrl+C

### Code Walkthrough

#### Imports (4 lines)

```python
import cv2                      # OpenCV - camera and image handling
import os                       # For creating folders
import time                     # For timing between captures
from datetime import datetime   # For timestamps in filenames
```

Each library has one job:
- **cv2**: Everything camera-related
- **os**: Create the output folder
- **time**: Sleep between captures
- **datetime**: Generate unique filenames

#### Configuration (5 lines)

```python
INTERVAL_SECONDS = 10      # Time between photos
WIDTH = 640                # Image width
HEIGHT = 480               # Image height
OUTPUT_FOLDER = "simple_data"
JPEG_QUALITY = 85
```

All settings at the top = easy to find and change.

#### Create Output Folder (2 lines)

```python
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
```

- `os.makedirs()` creates the folder (and any parent folders)
- `exist_ok=True` means "don't error if it already exists"

#### Open Camera (5 lines)

```python
cap = cv2.VideoCapture(0)     # 0 = first camera

if not cap.isOpened():
    print("ERROR: Could not open camera!")
    return

cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
```

Key points:
- `VideoCapture(0)` opens camera index 0 (first camera)
- **Always check** `isOpened()` - cameras can fail
- `cap.set()` configures resolution

#### Camera Warm-up (3 lines)

```python
for _ in range(5):
    cap.read()
    time.sleep(0.1)
```

Why? Cameras need time to adjust auto-exposure and white balance. First few frames are often too dark.

#### Capture Loop (15 lines)

```python
while True:
    ret, frame = cap.read()           # Capture frame
    
    if not ret:
        break
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{timestamp}.jpg"
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    
    # Save image
    cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    
    time.sleep(INTERVAL_SECONDS)      # Wait for next capture
```

The core loop:
1. `cap.read()` returns `(success, image)`
2. Generate timestamped filename
3. Save with `cv2.imwrite()`
4. Sleep until next capture

#### Cleanup (1 line)

```python
cap.release()
```

**Always release the camera** so other apps can use it.

---

## 🖥️ simple_with_preview.py - Adding a GUI

This extended script adds a **live preview window** so you can see what the camera sees.

### Quick Start

```bash
python simple_with_preview.py     # Start with preview
# Press ESC in preview window to stop
```

### Key Differences from simple.py

| Feature | simple.py | simple_with_preview.py |
|---------|-----------|------------------------|
| Preview window | ❌ No | ✅ Yes |
| Stop method | Ctrl+C | ESC key or Ctrl+C |
| Requires display | No | Yes |
| Code length | ~80 lines | ~130 lines |

### New Concepts

#### Continuous Frame Reading

```python
while True:
    ret, frame = cap.read()  # Read every iteration for smooth preview
    
    # Only SAVE when interval has passed
    if time_since_capture >= INTERVAL_SECONDS:
        cv2.imwrite(...)
```

Unlike `simple.py` which reads+saves+sleeps, this script reads continuously for smooth preview.

#### Drawing Text on Images

```python
cv2.putText(
    frame,                      # Image to draw on
    "Status text",              # Text string
    (10, 28),                   # Position (x, y)
    cv2.FONT_HERSHEY_SIMPLEX,   # Font
    0.6,                        # Font scale
    (0, 255, 0),                # Color (BGR format - Green)
    2                           # Line thickness
)
```

Note: OpenCV uses **BGR** color order, not RGB!

#### Showing a Window

```python
cv2.imshow("Window Title", frame)   # Display the frame
key = cv2.waitKey(1) & 0xFF         # Check for key press (1ms wait)

if key == 27:  # ESC key code
    break
```

- `imshow()` creates/updates a window
- `waitKey(1)` waits 1ms and returns pressed key code
- ESC key = code 27

#### Cleanup with Windows

```python
cap.release()
cv2.destroyAllWindows()   # Close all OpenCV windows
```

---

## 🔧 Customization Ideas

### Change capture interval

```python
INTERVAL_SECONDS = 30   # One photo every 30 seconds
```

### Use a different camera

```python
cap = cv2.VideoCapture(1)   # Use second camera
```

### Higher resolution

```python
WIDTH = 1920
HEIGHT = 1080
```

### Add date subfolders

```python
from datetime import datetime
date_folder = datetime.now().strftime("%Y-%m-%d")
OUTPUT_FOLDER = os.path.join("simple_data", date_folder)
```

---

## 🧠 What You've Learned

After studying these scripts:

| Concept | Code |
|---------|------|
| Open camera | `cv2.VideoCapture(0)` |
| Set resolution | `cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)` |
| Capture frame | `ret, frame = cap.read()` |
| Save image | `cv2.imwrite(path, frame)` |
| Show preview | `cv2.imshow(title, frame)` |
| Detect key press | `cv2.waitKey(1)` |
| Release resources | `cap.release()` |

---

## 📈 Next Steps

Ready for more? Explore the full application:

1. **[camera_opencv.py](../src/pitimelapse/camera_opencv.py)** - Production camera wrapper
2. **[capture.py](../src/pitimelapse/capture.py)** - Threaded background capture
3. **[app.py](../src/pitimelapse/app.py)** - Flask web interface

The full app adds:
- Web-based control (Flask)
- Background threads
- Session management
- Configuration files
- Error recovery

But at its core, it uses the same OpenCV calls you learned here!

---

## ❓ Troubleshooting

### "Could not open camera"
- Check camera is connected
- Close other apps using the camera (Zoom, Teams, etc.)
- Try `cv2.VideoCapture(1)` for USB cameras

### "Could not capture frame"
- Camera may have disconnected
- Check USB cable

### Preview window doesn't appear
- Use `simple.py` for headless systems
- Install `opencv-python` (not `opencv-python-headless`)

### ESC key doesn't work
- Click on the preview window first (it needs focus)
- The terminal won't receive ESC - use Ctrl+C there

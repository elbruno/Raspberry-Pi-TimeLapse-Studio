# PiTimeLapse Lab — Graphical Desktop App Plan
**Requested by:** Bruno Capuano  
**Date:** 2025-01-20  
**Prepared by:** Remy (Lead)

---

## 📋 Executive Summary

This document outlines the architecture and implementation plan for a **new graphical desktop application** that provides touch-screen time-lapse capture with automatic USB drive storage. This is a **separate application** from the existing Flask web app, designed specifically for standalone Raspberry Pi operation with a touchscreen display.

**Key Requirements:**
1. Graphical desktop app (NOT web-based)
2. Auto-detects and uses first external USB drive for storage
3. Live camera preview on touchscreen
4. Start/Stop buttons for 1-photo-per-second capture
5. Minimal, touch-friendly UI

---

## 🔍 Existing Codebase Analysis

### What Can Be Reused

#### **1. Camera Abstraction (✅ Full Reuse)**
- **Location:** `01 - WebApp TimeLapse/src/pitimelapse/camera_opencv.py`
- **Reusable Components:**
  - `OpenCVCamera` class with interface: `open()`, `capture()`, `close()`, `is_available()`
  - Optional dependency pattern with `OPENCV_AVAILABLE` flag
  - Camera warmup logic (3 frame captures)
  - Resolution handling (actual vs. requested)
  - Comprehensive error handling and logging
  - `save_image()` function for JPEG/PNG export with quality control
- **Why It Works:** The existing camera code is already cross-platform and well-tested. It handles OpenCV initialization, stderr suppression, and V4L2 backend fallback perfectly.

#### **2. Session & Storage Patterns (🔄 Adapt)**
- **Location:** `01 - WebApp TimeLapse/src/pitimelapse/storage.py` & `models.py`
- **Reusable Concepts:**
  - Session ID generation (timestamp-based)
  - Session folder creation pattern: `session_YYYYMMDD_HHMMSS/`
  - Image filename format: `img_0001_YYYYMMDD_HHMMSS.jpg`
  - `session.json` metadata persistence
  - Session model with `to_dict()` / `from_dict()` for JSON serialization
- **Modifications Needed:**
  - Change base directory from `./data` to auto-detected USB drive path
  - Add USB drive detection logic
  - Simplify metadata (no web-specific fields needed)

#### **3. Capture Loop Logic (🔄 Adapt)**
- **Location:** `01 - WebApp TimeLapse/src/pitimelapse/capture.py`
- **Reusable Concepts:**
  - Background thread capture with `threading.Event` for signaling
  - Retry logic (3 attempts on camera failure)
  - Status tracking (`Status` dataclass)
  - Thread-safe status updates with `threading.Lock`
- **Modifications Needed:**
  - Fixed 1-second interval (not configurable)
  - Simpler start/stop control (no web callback)
  - Integration with pygame event loop instead of Flask

#### **4. pygame UI Pattern (✅ Full Reuse)**
- **Location:** `labs/05-button-ui/button_ui.py`
- **Reusable Components:**
  - pygame initialization with framebuffer targeting (`SDL_FBDEV=/dev/fb0`)
  - Touch event handling (`pygame.MOUSEBUTTONDOWN`)
  - Button class with visual press feedback
  - 480x320 layout optimized for 3.5" LCD
  - Status message display with timeout fading
- **Why It Works:** This lab already demonstrates touch-friendly UI on the exact target hardware (Kuman SC06 LCD).

### What's Novel

1. **USB Drive Auto-Detection** — New logic needed to find and mount external drives
2. **Live Camera Preview in pygame** — Displaying OpenCV frames in pygame surface
3. **Integrated Capture + Display Loop** — Merging camera capture thread with pygame render loop
4. **Fixed 1-second Interval** — Simpler than configurable intervals but requires fast capture

---

## 🏗️ Proposed Architecture

### Technology Stack

#### **GUI Framework: pygame** ✅ RECOMMENDED

**Why pygame?**
- ✅ **Already validated** — Lab 05 proves it works on target hardware (Kuman SC06 3.5" LCD)
- ✅ **Framebuffer support** — Can run headless (no X11) via `/dev/fb0`
- ✅ **Touch input** — Native support for resistive touchscreen via SDL
- ✅ **Image display** — Easy to convert OpenCV (numpy) → pygame Surface
- ✅ **Minimal dependencies** — Already in `labs/requirements.txt`
- ✅ **Cross-platform** — Works on Windows/macOS/Linux for development

**Why NOT alternatives?**
- ❌ **tkinter** — Poor touchscreen support, not optimized for framebuffer, outdated look
- ❌ **PyQt5/PySide6** — Heavy dependencies (~300MB), overkill for simple UI, harder to deploy
- ❌ **Kivy** — Good for touch but adds complexity, not needed for 2-button UI
- ❌ **Direct framebuffer** — Too low-level, reinventing pygame's wheel

**Decision:** Use **pygame 2.x** with the same SDL configuration pattern as `labs/05-button-ui/`

---

### USB Drive Auto-Detection Strategy

#### **Primary Approach: psutil + heuristics**

```python
import psutil
from pathlib import Path

def find_first_usb_drive() -> str:
    """
    Detect first external USB drive.
    
    Strategy:
    1. List all mounted partitions with psutil.disk_partitions()
    2. Filter by:
       - mountpoint NOT in ["/", "/boot", "/boot/firmware"]
       - device path matches USB pattern: /dev/sd* (not /dev/mmcblk*)
       - filesystem type: vfat, exfat, ntfs, ext4
    3. Return first match's mountpoint
    
    Returns:
        Path to USB drive mountpoint, or "./data" fallback
    """
    for partition in psutil.disk_partitions():
        device = partition.device.lower()
        mount = partition.mountpoint
        
        # Skip system partitions
        if mount in ["/", "/boot", "/boot/firmware", "/home"]:
            continue
        
        # Raspberry Pi: USB drives are /dev/sda*, /dev/sdb*
        # SD card is /dev/mmcblk0*
        if "mmcblk" in device:
            continue
        
        # Check it's writable
        if os.access(mount, os.W_OK):
            return mount
    
    # Fallback to local directory
    return "./data"
```

**Pros:**
- ✅ Works on Linux (Raspberry Pi), Windows, macOS
- ✅ `psutil` is lightweight (already in `labs/requirements.txt`)
- ✅ No need for udev rules or sudo
- ✅ Detects dynamically at startup

**Cons:**
- ⚠️ Doesn't handle hot-plug (drive must be mounted at startup)
- ⚠️ No user confirmation (picks first drive automatically)

**Fallback Behavior:**
If no USB drive found → save to `./data` (same as web app)

#### **Alternative Approach: Manual mount path**
Add config option to override auto-detection:
```yaml
# In config file (optional)
usb_mount_path: /media/usb0  # Skip auto-detection
```

---

### Live Camera Preview Implementation

#### **Strategy: OpenCV → pygame Surface Conversion**

```python
def opencv_to_pygame(cv_frame):
    """
    Convert OpenCV BGR frame to pygame RGB surface.
    
    Steps:
    1. Convert BGR (OpenCV) to RGB (pygame)
    2. Transpose array (OpenCV is row-major, pygame expects column-major)
    3. Create pygame surface from array
    """
    import cv2
    import pygame
    import numpy as np
    
    # Convert BGR to RGB
    rgb_frame = cv2.cvtColor(cv_frame, cv2.COLOR_BGR2RGB)
    
    # Rotate if needed (transpose + flip for 90° rotation)
    # rgb_frame = cv2.rotate(rgb_frame, cv2.ROTATE_90_CLOCKWISE)
    
    # Convert to pygame surface
    surface = pygame.surfarray.make_surface(
        np.transpose(rgb_frame, (1, 0, 2))  # Swap width/height for pygame
    )
    
    return surface
```

**Preview Update Strategy:**
- Capture frame from camera every pygame loop iteration (~30 FPS)
- Scale to fit display area (preserve aspect ratio)
- Overlay UI elements (buttons, status) on top

**Performance Consideration:**
- OpenCV capture at 640x480 is fast (<30ms)
- 1-second interval gives plenty of time for display updates
- pygame can handle 30 FPS rendering at 480x320 easily

---

### Application Architecture

```
┌─────────────────────────────────────────────────┐
│         PiTimeLapse Touch App                   │
│  (labs/06-timelapse-touch/timelapse_touch.py)   │
└─────────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
  ┌─────────┐  ┌─────────┐  ┌──────────┐
  │ pygame  │  │ OpenCV  │  │  Storage │
  │  UI     │  │ Camera  │  │ Manager  │
  │ Loop    │  │ Thread  │  │ (USB)    │
  └─────────┘  └─────────┘  └──────────┘
       │            │             │
       └────────────┴─────────────┘
            Shared Status Object
            (thread-safe with Lock)
```

#### **Main Components**

**1. Main pygame Event Loop (Main Thread)**
- Initialize display (480x320)
- Render live camera preview
- Draw Start/Stop buttons
- Handle touch events
- Update status display (photo count, time)
- Run at 30 FPS

**2. Camera Preview (Main Thread)**
- Grab frame from camera every loop
- Convert to pygame surface
- Scale to preview area (preserve aspect ratio)
- Display in center of screen

**3. Capture Thread (Background Thread)**
- Runs when "Start" pressed
- Every 1 second:
  - Capture frame
  - Save to USB drive (JPEG)
  - Update photo count (thread-safe)
- Stops when "Stop" pressed or error

**4. USB Storage Manager**
- Detects USB drive at startup
- Creates session folder: `/media/usb0/session_20250120_143022/`
- Saves images: `img_0001_20250120_143022.jpg`
- Saves metadata: `session.json`
- Falls back to `./data` if no USB drive

**5. Status Object (Shared State)**
```python
@dataclass
class AppStatus:
    capturing: bool = False
    photo_count: int = 0
    usb_drive_path: str = ""
    last_error: str = ""
    session_id: str = ""
    lock: threading.Lock = field(default_factory=threading.Lock)
```

---

### UI Layout Design

```
┌─────────────────────────────────────────────────┐
│  PiTimeLapse Touch            USB: ✓  Photos: 0 │  ← Header (40px)
├─────────────────────────────────────────────────┤
│                                                 │
│                                                 │
│          [ Live Camera Preview ]                │  ← Preview (200px)
│              640x480 → fit                      │
│                                                 │
│                                                 │
├─────────────────────────────────────────────────┤
│   ┌───────────┐              ┌───────────┐     │
│   │   START   │              │   STOP    │     │  ← Buttons (60px)
│   │   ●       │              │   ■       │     │
│   └───────────┘              └───────────┘     │
├─────────────────────────────────────────────────┤
│  Status: Ready                                  │  ← Status bar (20px)
└─────────────────────────────────────────────────┘

Dimensions: 480 (W) × 320 (H)
```

**Layout Breakdown:**
- **Header:** 480x40 — Title, USB indicator, photo counter
- **Preview:** 480x200 — Live camera feed (scaled from 640x480)
- **Buttons:** Two 200x60 buttons side-by-side
- **Status Bar:** 480x20 — Current status message

**Color Scheme:**
- Background: Dark blue-gray `(15, 18, 30)` — from Lab 05
- Start button: Green `(50, 200, 80)` when idle, darker when capturing
- Stop button: Red `(200, 50, 50)` when capturing, gray when idle
- USB indicator: Green dot = detected, Red dot = missing

---

### Capture Loop Logic

```python
def capture_thread_worker(camera, status, storage):
    """
    Background thread that captures photos every 1 second.
    """
    while True:
        with status.lock:
            if not status.capturing:
                time.sleep(0.1)  # Wait for start signal
                continue
        
        try:
            # Capture frame
            frame = camera.capture()
            if frame is None:
                raise Exception("Camera capture failed")
            
            # Save to USB drive
            filename = storage.get_next_filename()
            filepath = os.path.join(status.usb_drive_path, status.session_id, filename)
            save_image(frame, filepath, quality=85)
            
            # Update status (thread-safe)
            with status.lock:
                status.photo_count += 1
            
            # Wait exactly 1 second from capture start
            time.sleep(1.0)
            
        except Exception as e:
            with status.lock:
                status.last_error = str(e)
                status.capturing = False
            break
```

**Key Points:**
- Separate thread prevents UI blocking
- 1-second interval is fixed
- Errors stop capture and display in UI
- Thread checks status.capturing flag each loop

---

## 📂 Proposed File Organization

### Directory Structure

```
labs/
├── 06-timelapse-touch/              ← NEW APP
│   ├── timelapse_touch.py           ← Main application
│   ├── camera_opencv.py             ← Symlink/copy from web app
│   ├── storage_manager.py           ← USB-aware storage (new)
│   ├── ui_components.py             ← Button, StatusBar classes
│   ├── usb_detector.py              ← USB drive detection logic
│   ├── config.yaml                  ← Optional config file
│   └── README.md                    ← Installation & usage
├── requirements.txt                 ← Shared dependencies (update)
└── README.md                        ← Update with Lab 06 entry

01 - WebApp TimeLapse/               ← EXISTING (unchanged)
    └── src/pitimelapse/
        ├── camera_opencv.py         ← SOURCE for camera code
        ├── storage.py               ← Inspiration for storage
        └── models.py                ← Inspiration for Session model
```

### Files to Create

| File | Purpose | Lines | Reuse From |
|------|---------|-------|------------|
| `timelapse_touch.py` | Main application entry point | ~400 | Lab 05 structure |
| `camera_opencv.py` | Camera abstraction | ~50 | Copy from web app or import |
| `storage_manager.py` | USB storage with auto-detection | ~200 | Adapt from `storage.py` |
| `ui_components.py` | Button, StatusBar, PreviewPanel classes | ~150 | Lab 05 Button class |
| `usb_detector.py` | USB drive detection logic | ~100 | New (psutil-based) |
| `config.yaml` | Optional config overrides | ~20 | Simplified from web app |
| `README.md` | Installation & usage docs | ~150 | Follow lab pattern |

**Total New Code:** ~1070 lines (but 50% is adapted/copied)

---

## 🔧 Dependencies

### Python Packages (add to `labs/requirements.txt`)

```txt
# Existing
pygame>=2.0.0
psutil>=5.9.0
Pillow>=9.0.0

# New for Lab 06
opencv-python-headless>=4.8.0  # Camera capture
PyYAML>=6.0                    # Config file (optional)
```

**Note:** `opencv-python-headless` vs `opencv-python`
- Use **headless** for production (no GUI dependencies)
- Use **full** for development (includes highgui for debugging)

### System Dependencies (Raspberry Pi)

```bash
# Already installed if web app works
sudo apt install python3-opencv  # Alternative to pip install
```

---

## 📝 Implementation Plan

### Phase 1: Core Infrastructure (Day 1)

#### **Step 1.1: Create Lab 06 Directory Structure**
- [x] Create `labs/06-timelapse-touch/` folder
- [ ] Copy `camera_opencv.py` from web app (or use import path)
- [ ] Create `README.md` with hardware requirements
- [ ] Update `labs/README.md` with Lab 06 entry

#### **Step 1.2: USB Drive Detection**
- [ ] Create `usb_detector.py`:
  - `find_first_usb_drive()` function using psutil
  - Test on Raspberry Pi with USB stick
  - Test fallback behavior (no USB)
  - Add logging for detected drives
- [ ] Unit tests for USB detection logic

#### **Step 1.3: Storage Manager**
- [ ] Create `storage_manager.py`:
  - `USBStorageManager` class
  - Session folder creation on USB
  - Image filename generation (1-second interval)
  - `session.json` metadata saving
  - Handle USB write errors gracefully
- [ ] Test with mock USB drive path

**Deliverable:** USB detection works, can create session folders

---

### Phase 2: Camera Integration (Day 2)

#### **Step 2.1: Camera Preview Conversion**
- [ ] Add `opencv_to_pygame()` function:
  - BGR → RGB conversion
  - Numpy array → pygame Surface
  - Scaling/aspect ratio preservation
  - Optional rotation for LCD orientation
- [ ] Test standalone: capture → display → save loop

#### **Step 2.2: Capture Thread**
- [ ] Create `capture_worker()` function:
  - Background thread with 1-second loop
  - Thread-safe status updates
  - Camera open/close lifecycle
  - Error handling with retry logic
  - Graceful shutdown on stop signal

**Deliverable:** Camera can capture and save to USB every 1 second

---

### Phase 3: UI Development (Day 3)

#### **Step 3.1: UI Components**
- [ ] Create `ui_components.py`:
  - `Button` class (from Lab 05, with icons)
  - `StatusBar` class
  - `Header` class (title + indicators)
  - `PreviewPanel` class (camera feed display)
- [ ] Add touch feedback animations
- [ ] Add visual states (idle, capturing, error)

#### **Step 3.2: Main Application**
- [ ] Create `timelapse_touch.py`:
  - pygame initialization (framebuffer mode)
  - Event loop (30 FPS)
  - Camera preview rendering
  - Start/Stop button handlers
  - Status display updates
  - Thread lifecycle management
- [ ] Add keyboard shortcuts for development:
  - `S` = Start
  - `Space` = Stop
  - `Q` or `ESC` = Quit

**Deliverable:** Full working app with touch UI

---

### Phase 4: Testing & Polish (Day 4)

#### **Step 4.1: Hardware Testing**
- [ ] Test on Raspberry Pi with 3.5" LCD touchscreen
- [ ] Test with USB drive (various filesystems)
- [ ] Test USB hot-plug behavior (warning message)
- [ ] Test camera failure recovery
- [ ] Test disk full scenario

#### **Step 4.2: Error Handling**
- [ ] Add error modals/messages:
  - No USB drive detected → fallback message
  - Camera not available → error screen
  - Disk full → stop capture, show warning
  - Camera disconnected → retry + error message

#### **Step 4.3: Documentation**
- [ ] Complete `README.md`:
  - Hardware requirements
  - Installation steps
  - Configuration options
  - Troubleshooting
  - Screenshots
- [ ] Add inline code comments
- [ ] Create user manual (simple PDF?)

**Deliverable:** Production-ready app with docs

---

## ❓ Open Questions & Design Decisions

### Question 1: Camera Preview Frame Rate
**Options:**
- A) Capture preview frame every loop (~30 FPS) — smooth but CPU-intensive
- B) Capture preview frame every 5 loops (~6 FPS) — choppy but efficient
- C) Use separate preview thread — complex but optimal

**Recommendation:** **Option A** — Modern Pi (3B+/4/5) can handle 30 FPS at 640x480. If performance issues arise, fall back to Option B.

**Decision needed from Bruno:** What's the target Raspberry Pi model? (Affects performance budget)

---

### Question 2: USB Drive Selection UI
**Options:**
- A) Auto-select first USB drive (silent) — simple but inflexible
- B) Auto-select + show detected path in header — transparent
- C) Show selection dialog on startup — user control but complex

**Recommendation:** **Option B** — Display USB mount path in header (`USB: /media/usb0 ✓`). Simple + transparent.

**Decision needed from Bruno:** Should user be able to override auto-detection? (Add config file option?)

---

### Question 3: Session Resume Behavior
**Scenario:** App crashes mid-capture. What should happen on restart?

**Options:**
- A) Always start new session — data loss but simple
- B) Detect incomplete session, ask to resume — complex UX
- C) Auto-resume last session — seamless but risky

**Recommendation:** **Option A** for V1, add Option B in future release.

**Decision needed from Bruno:** Is session resume a V1 requirement or future enhancement?

---

### Question 4: Configuration File
**Question:** Should the app support `config.yaml` for customization?

**Possible Settings:**
```yaml
# Optional configuration overrides
camera_index: 0                  # Which camera (default: 0)
resolution_width: 640            # Default: 640
resolution_height: 480           # Default: 480
usb_mount_override: null         # Manual USB path (default: auto)
image_format: jpg                # jpg or png
jpeg_quality: 85                 # 0-100
session_name_prefix: "session"   # Default: "session"
```

**Recommendation:** Add config file support but make it **optional**. App works out-of-box with defaults.

**Decision needed from Bruno:** Are any settings needed beyond defaults?

---

### Question 5: Pi Camera (picamera2) Support
**Question:** Should we add Pi Camera module support (like web app)?

**Pros:**
- Higher quality than USB webcams
- Better control (exposure, white balance)

**Cons:**
- Adds complexity (optional dependency)
- Not needed if USB camera works well

**Recommendation:** **Start with OpenCV only** (USB webcam). Add picamera2 in V2 if needed.

**Decision needed from Bruno:** Is Pi Camera Module a must-have or nice-to-have?

---

## 🎯 Success Criteria

### Must-Have (V1)
- ✅ App runs on Raspberry Pi with 3.5" touchscreen
- ✅ Auto-detects and uses first USB drive
- ✅ Shows live camera preview
- ✅ Start button begins 1-photo-per-second capture
- ✅ Stop button ends capture
- ✅ Photos saved to USB in session folders
- ✅ Clear error messages if USB/camera missing
- ✅ Touch-friendly button sizes (>50px)

### Nice-to-Have (Future)
- 🔲 Configurable capture interval (not fixed to 1s)
- 🔲 Gallery view of captured photos
- 🔲 Wi-Fi transfer of photos
- 🔲 Session resume after crash
- 🔲 Pi Camera module support
- 🔲 Timelapse video generation

### Performance Targets
- Preview lag: <100ms
- Touch response: <50ms
- Capture save time: <200ms (to not delay next capture)
- Memory usage: <150MB
- CPU usage: <50% on Pi 3B+

---

## 🚀 Estimated Timeline

| Phase | Duration | Blockers |
|-------|----------|----------|
| 1. Core Infrastructure | 1 day | Need USB drive for testing |
| 2. Camera Integration | 1 day | Need camera hardware |
| 3. UI Development | 1 day | Need touchscreen LCD |
| 4. Testing & Polish | 1 day | Need complete hardware setup |
| **Total** | **4 days** | Assumes hardware available |

**Development Environment:**
- Days 1-2: Can develop on laptop (USB drive, webcam)
- Day 3: Need Raspberry Pi with touchscreen
- Day 4: Full hardware integration testing

---

## 📦 Deliverables Checklist

### Code
- [ ] `labs/06-timelapse-touch/timelapse_touch.py` — Main app
- [ ] `labs/06-timelapse-touch/camera_opencv.py` — Camera module
- [ ] `labs/06-timelapse-touch/storage_manager.py` — USB storage
- [ ] `labs/06-timelapse-touch/ui_components.py` — UI classes
- [ ] `labs/06-timelapse-touch/usb_detector.py` — Drive detection
- [ ] `labs/06-timelapse-touch/config.yaml` — Optional config
- [ ] Updated `labs/requirements.txt` — Add opencv-python-headless

### Documentation
- [ ] `labs/06-timelapse-touch/README.md` — Installation & usage
- [ ] Updated `labs/README.md` — Add Lab 06 entry
- [ ] Code comments and docstrings
- [ ] Troubleshooting section in README

### Testing
- [ ] Manual test checklist (hardware scenarios)
- [ ] Unit tests for USB detection
- [ ] Unit tests for storage manager
- [ ] Integration test script (camera + USB + display)

---

## 📖 Related Resources

### Existing Codebase References
- **Camera code:** `01 - WebApp TimeLapse/src/pitimelapse/camera_opencv.py`
- **Storage patterns:** `01 - WebApp TimeLapse/src/pitimelapse/storage.py`
- **Session model:** `01 - WebApp TimeLapse/src/pitimelapse/models.py`
- **pygame UI:** `labs/05-button-ui/button_ui.py`
- **LCD setup:** `labs/README.md` (driver installation)

### External Documentation
- [pygame Documentation](https://www.pygame.org/docs/)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [psutil Documentation](https://psutil.readthedocs.io/)
- [Raspberry Pi Camera Guide](https://www.raspberrypi.com/documentation/computers/camera_software.html)

---

## 🎬 Next Steps

**Immediate Actions for Bruno:**
1. **Review this plan** — Provide feedback on architecture decisions
2. **Answer open questions** — See section "Open Questions & Design Decisions"
3. **Confirm hardware** — Verify Pi model, LCD, USB drive availability
4. **Approve timeline** — 4-day estimate work for your schedule?
5. **Prioritize features** — Must-have vs. nice-to-have for V1

**Once Approved:**
1. **Create lab folder structure** — Set up files and skeleton code
2. **Implement USB detection** — First working module
3. **Daily check-ins** — Progress reports and blocker resolution
4. **Hardware testing sessions** — Coordinated remote testing

---

**Last Updated:** 2025-01-20  
**Status:** Awaiting Bruno's feedback  
**Questions?** Contact Remy via GitHub issues or team chat

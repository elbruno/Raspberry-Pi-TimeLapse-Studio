# Graphical Desktop App — Quick Summary
**For:** Bruno Capuano  
**Prepared by:** Remy  
**Date:** 2025-01-20

---

## 🎯 What You Asked For

A **graphical desktop app** (not web) for Raspberry Pi + touchscreen that:
1. Auto-detects and uses 1st USB drive for storage
2. Shows live camera preview
3. Has Start/Stop buttons for 1-photo-per-second capture
4. Minimal, touch-friendly UI

---

## ✅ What Can Be Reused

### 60-70% of Existing Code Works!

| Component | Reusable? | Source |
|-----------|-----------|--------|
| **Camera Logic** | ✅ 100% | `camera_opencv.py` from web app |
| **Storage Patterns** | 🔄 90% | `storage.py` + `models.py` (adapt for USB) |
| **Capture Thread** | 🔄 80% | `capture.py` (simplify for fixed 1s interval) |
| **Touch UI Pattern** | ✅ 100% | Lab 05 `button_ui.py` |

**Translation:** Most code is copy-paste with minor tweaks. Focus on 3 new pieces:
1. USB drive auto-detection
2. Camera preview in pygame
3. Wiring it all together

---

## 🏗️ Recommended Tech Stack

### GUI Framework: **pygame** ✅

**Why?**
- Already works on your hardware (Lab 05 proves it)
- Touch support built-in
- Runs headless (no X11 needed)
- Lightweight (already installed)

**Alternatives considered and rejected:**
- tkinter → poor touch support
- PyQt5 → too heavy (300MB)
- Kivy → unnecessary complexity

### USB Detection: **psutil** ✅

```python
import psutil

def find_usb_drive():
    for partition in psutil.disk_partitions():
        if "/dev/sd" in partition.device:  # USB on Pi
            if partition.mountpoint not in ["/", "/boot"]:
                return partition.mountpoint
    return "./data"  # Fallback
```

**Pros:** Cross-platform, lightweight, no sudo needed  
**Cons:** No hot-plug (drive must be mounted at startup)

---

## 📐 UI Layout

```
┌────────────────────────────────────────────┐
│ PiTimeLapse Touch    USB: ✓   Photos: 42  │ ← Header
├────────────────────────────────────────────┤
│                                            │
│       [ Live Camera Preview ]              │ ← 480x200 preview
│                                            │
├────────────────────────────────────────────┤
│   ┌──────────┐         ┌──────────┐       │
│   │  START   │         │   STOP   │       │ ← Buttons
│   │    ●     │         │    ■     │       │
│   └──────────┘         └──────────┘       │
├────────────────────────────────────────────┤
│ Status: Capturing...                       │ ← Status bar
└────────────────────────────────────────────┘
```

---

## 📁 New Files (7 files, ~1000 lines total)

```
labs/06-timelapse-touch/
├── timelapse_touch.py      ← Main app (400 lines)
├── camera_opencv.py        ← Copy from web app (50 lines)
├── storage_manager.py      ← USB storage (200 lines)
├── ui_components.py        ← Button/StatusBar classes (150 lines)
├── usb_detector.py         ← USB auto-detect (100 lines)
├── config.yaml             ← Optional config (20 lines)
└── README.md               ← Docs (150 lines)
```

---

## ⏱️ Timeline: **4 Days**

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | USB detection + storage | Can create folders on USB |
| 2 | Camera integration | Camera captures to USB every 1s |
| 3 | UI development | Full working app with touch |
| 4 | Testing & polish | Production-ready with docs |

**Hardware Needed:**
- Days 1-2: Laptop + USB drive + webcam
- Days 3-4: Raspberry Pi + touchscreen LCD

---

## ❓ 5 Questions for You

### 1. Camera Preview Frame Rate
- **Option A:** 30 FPS (smooth but CPU-intensive)
- **Option B:** 6 FPS (choppy but efficient)

**Recommendation:** Try A first, fall back to B if Pi lags  
**Your decision:** _______

### 2. USB Drive Selection
- **Option A:** Auto-select first, show path in header
- **Option B:** Show selection dialog on startup

**Recommendation:** Option A (simpler)  
**Your decision:** _______

### 3. Session Resume After Crash?
- **Option A:** Always start new session (simple)
- **Option B:** Detect + ask to resume (complex)

**Recommendation:** A for V1, B later  
**Your decision:** _______

### 4. Config File Needed?
Settings like camera index, resolution, JPEG quality?

**Recommendation:** Optional config, works with defaults  
**Your decision:** Yes / No

### 5. Pi Camera Module Support?
Add picamera2 support (like web app)?

**Recommendation:** Start with USB camera only  
**Your decision:** Now / Later / Never

---

## 📊 What's Next?

### If You Approve This Plan:

1. **I'll create the lab folder** and skeleton files
2. **Implement USB detection** (Day 1 deliverable)
3. **Daily progress reports** with screenshots
4. **Request hardware testing** when UI is ready

### If You Want Changes:

1. **Review full plan:** `.squad/graphical-app-plan.md`
2. **Answer the 5 questions above**
3. **Request any architecture changes**
4. **I'll revise and re-submit**

---

## 📋 Success Criteria

### Must Work:
- ✅ Runs on Pi with 3.5" touchscreen
- ✅ Auto-uses USB drive
- ✅ Live preview visible
- ✅ Start/Stop buttons responsive
- ✅ Photos save to USB every 1s
- ✅ Clear errors if USB/camera missing

### Performance:
- Touch response < 50ms
- Capture save time < 200ms
- Memory usage < 150MB

---

## 📞 Contact

**Questions?** Reply to this task or ping me in team chat.

**Ready to start?** Just say "approved" and I'll begin Day 1! 🚀

---

**Full plan:** See `.squad/graphical-app-plan.md` (25KB, detailed architecture)

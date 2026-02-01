# 📷 Hardware & Camera Basics

This document explains the hardware side of PiTimeLapse Lab - the Raspberry Pi and cameras.

## The Raspberry Pi

The Raspberry Pi is a small, affordable computer about the size of a credit card. It can run a full operating system (Linux) and is perfect for projects like this!

### Raspberry Pi Models

Different models work with this project:

| Model | RAM | Camera Port | Recommended? |
|-------|-----|-------------|--------------|
| Raspberry Pi 5 | 4-8 GB | Yes | ✅ Best |
| Raspberry Pi 4 | 2-8 GB | Yes | ✅ Great |
| Raspberry Pi 3B+ | 1 GB | Yes | ✅ Good |
| Raspberry Pi Zero 2 W | 512 MB | Yes (mini) | ⚠️ Limited |

### Key Parts of a Raspberry Pi

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │   🔌 USB Ports (for webcam, keyboard, etc.)           │  │
│  │                                                       │  │
│  │   🌐 Ethernet Port (wired network)                    │  │
│  │                                                       │  │
│  │   📹 Camera Connector (ribbon cable)                  │  │
│  │                                                       │  │
│  │   🔲 GPIO Pins (for electronics projects)             │  │
│  │                                                       │  │
│  │   💿 microSD Card Slot (storage)                      │  │
│  │                                                       │  │
│  │   ⚡ Power (USB-C on newer models)                    │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Camera Options

You have two main options for cameras:

### Option 1: Raspberry Pi Camera Module

This is the official camera that connects directly to the Pi.

**Pros:**
- Best image quality
- Most efficient (uses less CPU)
- Designed for the Pi
- Small and compact

**Cons:**
- Only works with Raspberry Pi
- Requires careful handling of ribbon cable
- Costs more than basic webcams

**Models:**
- Camera Module 3 (latest, autofocus)
- Camera Module 2 (older but good)
- HQ Camera (for serious photography)

### Option 2: USB Webcam

Any standard USB webcam works via OpenCV.

**Pros:**
- Works on any computer (not just Pi)
- Easy to set up (just plug in!)
- Many price options
- Can test on your laptop first

**Cons:**
- Uses more CPU power
- Image quality varies
- Takes up a USB port

## How Digital Cameras Work

Understanding camera basics helps with taking better time-lapses.

### Pixels and Resolution

An image is made of tiny dots called **pixels**. Resolution is how many pixels there are.

```
Resolution    Pixels           Use Case
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
640×480       307,200          Low quality, small files
1280×720      921,600          HD, good balance
1920×1080     2,073,600        Full HD, larger files
3840×2160     8,294,400        4K, huge files
```

Higher resolution = better quality but bigger files and more processing.

### How a Camera Captures an Image

1. **Light** comes through the lens
2. **Sensor** converts light to electrical signals
3. **Processor** converts signals to pixel data
4. **Software** saves data as an image file

```
Light → Lens → Sensor → Processor → Image File
  📸      🔍      ⚡        💻          🖼️
```

## Camera Settings Explained

### Resolution

The size of the captured images in pixels.

```yaml
# In config.yaml
resolution_width: 1280
resolution_height: 720
```

**Trade-offs:**
- Higher resolution = More detail, larger files
- Lower resolution = Smaller files, faster capture

### Image Format

How the image data is stored.

```yaml
image_format: "jpg"  # or "png"
```

**JPG (JPEG):**
- Compressed (smaller files)
- Slight quality loss
- Good for most uses

**PNG:**
- Not compressed
- Perfect quality
- Much larger files

## The Camera in Our Code

### camera_opencv.py

Uses OpenCV library for USB webcams:

```python
import cv2

class OpenCVCamera:
    def __init__(self):
        self.cap = None
    
    def open(self, width=1280, height=720):
        # Open the camera
        self.cap = cv2.VideoCapture(0)  # 0 = first camera
        
        # Set resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        return self.cap.isOpened()
    
    def capture(self):
        # Take a photo
        ret, frame = self.cap.read()
        if ret:
            return frame  # Return the image
        return None
    
    def close(self):
        # Release the camera
        self.cap.release()
```

### camera_picamera2.py

Uses picamera2 library for Pi Camera:

```python
from picamera2 import Picamera2

class PiCamera2Camera:
    def __init__(self):
        self.camera = None
    
    def open(self, width=1280, height=720):
        self.camera = Picamera2()
        config = self.camera.create_still_configuration(
            main={"size": (width, height)}
        )
        self.camera.configure(config)
        self.camera.start()
        return True
    
    def capture(self):
        return self.camera.capture_array()
    
    def close(self):
        self.camera.stop()
```

### How the Code Chooses

The app reads `camera_mode` from config and uses the right camera:

```python
# From capture.py
if self.config.camera_mode == "picamera2":
    from .camera_picamera2 import PiCamera2Camera
    self.camera = PiCamera2Camera()
else:
    from .camera_opencv import OpenCVCamera
    self.camera = OpenCVCamera()
```

## Troubleshooting Cameras

### USB Webcam Not Found

```bash
# List connected USB devices
lsusb

# Check if video device exists
ls -la /dev/video*

# Test with v4l2 tools
v4l2-ctl --list-devices
```

**Fixes:**
- Try a different USB port
- Unplug and replug the webcam
- Check if another program is using it

### Pi Camera Not Working

```bash
# Check if camera is detected
libcamera-hello --list-cameras

# Test the camera
libcamera-hello

# Check for errors
dmesg | grep -i camera
```

**Fixes:**
- Reseat the ribbon cable (gently!)
- Enable camera in raspi-config
- Reboot after changes

### Permission Denied

```bash
# Add your user to the video group
sudo usermod -aG video $USER

# Log out and log back in for changes to take effect
```

## Tips for Better Time-lapses

### 1. Stable Mounting

Keep the camera perfectly still. Any movement ruins the effect.

- Use a tripod
- Tape the camera down
- Use a phone/camera mount

### 2. Consistent Lighting

Big changes in lighting cause flickering in the final video.

- Shoot outdoors (natural light is more consistent)
- Or use artificial lighting you can control
- Avoid mixing light sources

### 3. Choose the Right Interval

| Subject | Suggested Interval |
|---------|-------------------|
| Clouds | 3-5 seconds |
| Sunset/sunrise | 5-10 seconds |
| Plants growing | 5-15 minutes |
| Construction | 1-10 minutes |
| Melting ice | 10-30 seconds |

### 4. Calculate Storage Needs

```
Photos × Size per photo = Total storage

Example:
- 24 hours at 10-second intervals = 8,640 photos
- Each photo ≈ 200 KB (1280×720 JPG)
- Total: 8,640 × 200 KB = 1.7 GB
```

### 5. Keep the Pi Powered

- Use a reliable power supply
- For outdoor use, consider battery + solar
- Use a UPS for protection against outages

## Making a Video from Your Time-lapse

Once you have captured images, you can make a video!

### Using FFmpeg

FFmpeg is a free tool for video processing:

```bash
# Install FFmpeg
sudo apt install ffmpeg

# Create video from images
ffmpeg -framerate 30 -pattern_type glob -i '*.jpg' \
       -c:v libx264 -pix_fmt yuv420p timelapse.mp4
```

This plays 30 images per second, creating smooth video.

### Frame Rate Explained

Frame rate is how many images show per second in the video:

- 24 fps = Cinema-like
- 30 fps = Standard video
- 60 fps = Smooth/sports

If you captured 600 images:
- At 30 fps: 600 ÷ 30 = 20 seconds of video
- At 60 fps: 600 ÷ 60 = 10 seconds of video

## Resources

- [Raspberry Pi Camera Documentation](https://www.raspberrypi.com/documentation/accessories/camera.html)
- [OpenCV Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [Time-lapse Photography Tips](https://www.digitalcameraworld.com/tutorials/time-lapse-photography-tips)

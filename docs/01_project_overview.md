# 📚 Project Overview

Welcome to **PiTimeLapse Lab**! This document explains what this project is about and how all the pieces fit together.

## What is a Time-lapse?

A **time-lapse** is a photography technique where you take many photos over a long period of time (hours, days, or even weeks), then play them back quickly like a video.

**Examples of cool time-lapses:**
- 🌅 A sunset over a few hours
- 🌸 A flower blooming over several days
- 🏗️ A building being constructed over months
- ☁️ Clouds moving across the sky
- 🌱 A plant growing from seed

Normally, these changes happen too slowly for our eyes to notice. But when you speed them up, they become magical!

## How This Project Works

PiTimeLapse Lab is a complete system for creating time-lapses using a Raspberry Pi. Here's the big picture:

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR COMPUTER                            │
│                                                                 │
│   Web Browser ◄──────────────────────────────────────┐          │
│   (Firefox, Chrome, etc.)                            │          │
│                                                      │          │
└──────────────────────────────────────────────────────┼──────────┘
                                                       │
                                                  Wi-Fi/Network
                                                       │
┌──────────────────────────────────────────────────────▼──────────┐
│                      RASPBERRY PI                               │
│                                                                 │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                    PiTimeLapse Lab                       │  │
│   │                                                          │  │
│   │   ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │  │
│   │   │  Web UI  │◄──►│ Flask    │◄──►│ Capture Scheduler│   │  │
│   │   │ (HTML/   │    │ Server   │    │                  │   │  │
│   │   │  CSS)    │    │          │    │  Takes photos    │   │  │
│   │   └──────────┘    └──────────┘    │  at intervals    │   │  │
│   │                                    └────────┬─────────┘   │  │
│   │                                             │             │  │
│   │   ┌──────────────────────────────┐          │             │  │
│   │   │         Storage              │◄─────────┘             │  │
│   │   │   (saves images to disk)     │                        │  │
│   │   └──────────────────────────────┘                        │  │
│   │                                                          │  │
│   └──────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          ▼                                      │
│   ┌──────────────────────────────────────────────────────────┐  │
│   │                      Camera                              │  │
│   │   (Pi Camera Module or USB Webcam)                       │  │
│   └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

Here's how the files are organized:

```
PiTimeLapse-Lab/
│
├── main.py                 # 🚀 The entry point - run this to start!
├── config.yaml             # ⚙️ Your settings (edit this!)
├── requirements.txt        # 📦 Python packages needed
│
├── src/pitimelapse/        # 💻 The main code
│   ├── app.py              #     Web server (Flask)
│   ├── config.py           #     Settings management
│   ├── capture.py          #     Photo capture scheduler
│   ├── camera_opencv.py    #     USB webcam support
│   ├── camera_picamera2.py #     Pi Camera support
│   ├── storage.py          #     File management
│   ├── overlay.py          #     Timestamp on images
│   ├── models.py           #     Data structures
│   └── utils.py            #     Helper functions
│
├── templates/              # 🎨 HTML pages
│   ├── base.html           #     Common layout
│   ├── index.html          #     Dashboard
│   ├── gallery.html        #     View photos
│   └── settings.html       #     Edit settings
│
├── static/                 # 🖌️ Styles
│   └── style.css           #     CSS for the web pages
│
├── tests/                  # 🧪 Automated tests
│   ├── test_config.py
│   ├── test_utils.py
│   └── test_storage.py
│
├── docs/                   # 📖 Documentation (you're reading it!)
│   ├── 01_project_overview.md
│   ├── 02_python_basics_used.md
│   ├── 03_web_basics_flask.md
│   ├── 04_hardware_camera_basics.md
│   └── 05_extensions_challenges.md
│
└── data/                   # 📁 Where your photos are saved
    └── (session folders)
```

## Key Concepts

### Sessions

A **session** is one time-lapse recording. When you press "Start", a new session begins. When you press "Stop", it ends.

Each session has:
- A unique ID (like `session_20240115_143022`)
- Its own folder for images
- A JSON file with information about the session
- The captured photos

### The Capture Loop

The "capture loop" is the heart of the program. It runs in the background and:

1. Waits for the specified interval (e.g., 10 seconds)
2. Takes a photo
3. Adds a timestamp overlay (if enabled)
4. Saves the image to disk
5. Updates the session information
6. Repeats until you stop it

### The Web Interface

Instead of using the command line, you can control everything through a web browser:

- **Dashboard**: See if it's running, start/stop capture
- **Gallery**: View your captured images
- **Settings**: Change camera settings, intervals, etc.

## What You'll Learn

Building and using this project teaches you:

1. **Python Programming** - Variables, functions, classes, modules
2. **Web Development** - HTML, CSS, Flask framework
3. **Hardware** - Cameras, Raspberry Pi
4. **Software Design** - How to organize code into modules
5. **Testing** - Writing tests to make sure code works
6. **Version Control** - Using Git to track changes

## Next Steps

Ready to learn more? Check out these documents:

- [02 - Python Basics Used](02_python_basics_used.md) - Learn the Python concepts we use
- [03 - Web Basics with Flask](03_web_basics_flask.md) - Understand how the web interface works
- [04 - Hardware & Camera Basics](04_hardware_camera_basics.md) - Learn about cameras and hardware
- [05 - Extensions & Challenges](05_extensions_challenges.md) - Ideas to make the project your own!

Happy time-lapsing! 📸

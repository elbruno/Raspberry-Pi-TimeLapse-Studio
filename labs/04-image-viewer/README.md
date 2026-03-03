# Lab 04 — Image Viewer

Browse images on the Waveshare 3.5" RPi LCD (A) with touch navigation.

## What It Does

- Loads images from a folder (default: `./images/`)
- Scales images to fit 480×320 while preserving aspect ratio
- Tap the **right half** of the screen → next image
- Tap the **left half** → previous image
- Shows filename and image counter

## Prerequisites

- Waveshare LCD driver installed (`sudo ./LCD35-show`)
- Python 3 with pygame and Pillow: `pip install pygame Pillow`

## How to Run

```bash
# Place images in the images/ subfolder, then:
python image_viewer.py

# Or specify a custom folder:
python image_viewer.py /home/pi/photos
```

## Sample Images

Create an `images/` subfolder and place `.jpg` or `.png` files there. The viewer will display them in alphabetical order.

## What to Expect

Images appear centered on the LCD. Tap left/right sides to navigate. If no images are found, a help message is displayed.

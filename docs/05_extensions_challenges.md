# 🚀 Extensions & Challenges

Ready to take PiTimeLapse Lab further? Here are ideas to extend the project and challenges to test your skills!

## Beginner Challenges ⭐

### 1. Change the Colors

**Goal:** Make the web interface your own color scheme.

**Steps:**
1. Open `static/style.css`
2. Find the color values (like `#4CAF50` for green)
3. Change them to colors you like
4. Refresh the page to see your changes

**Tips:**
- Use [ColorHunt](https://colorhunt.co/) for color palettes
- CSS color names: `red`, `blue`, `coral`, `steelblue`, etc.
- Hex codes: `#FF5733`, `#3498DB`, etc.

### 2. Add Your Name

**Goal:** Add a footer credit with your name.

**Steps:**
1. Open `templates/base.html`
2. Find the `<footer>` section
3. Add your name: `Made by [Your Name]`

### 3. Custom Status Messages

**Goal:** Change the status messages to be more fun.

**Steps:**
1. Open `templates/index.html`
2. Find `Time-lapse Running` and `Ready to Start`
3. Change them to something creative like:
   - "📸 Capturing the moment..."
   - "😴 Waiting for action..."

## Intermediate Challenges ⭐⭐

### 4. Add a Pause Button

**Goal:** Add the ability to pause (not stop) the time-lapse.

**Hints:**
1. Add a `pause()` method to `CaptureScheduler` in `capture.py`
2. Add a pause/resume state to the `Status` class
3. Add an API endpoint: `POST /api/pause`
4. Add a button to the UI

**Skeleton code:**
```python
# In capture.py
def pause(self):
    """Pause the capture without ending the session."""
    if not self.status.is_running:
        return False, "Nothing to pause"
    
    self._paused = True
    return True, "Capture paused"

def resume(self):
    """Resume a paused capture."""
    if not self._paused:
        return False, "Not paused"
    
    self._paused = False
    return True, "Capture resumed"
```

### 5. Photo Counter Display

**Goal:** Show a live counter of photos on the dashboard that updates without refreshing.

**Hints:**
- The JavaScript already polls `/api/status` every 5 seconds
- Update the `#total-photos` element with the new count
- Add an animation when the count changes

### 6. Session Delete Button

**Goal:** Add a way to delete old sessions from the Gallery page.

**Steps:**
1. Add a delete button next to each session in the dropdown
2. Create an API endpoint: `DELETE /api/sessions/<id>`
3. Use the existing `storage.delete_session()` method
4. Confirm before deleting!

### 7. Dark Mode

**Goal:** Add a toggle for dark/light theme.

**Hints:**
- Create a dark theme in CSS using CSS variables
- Store the preference in localStorage
- Toggle a class on `<body>` to switch themes

**CSS Variables example:**
```css
:root {
  --bg-color: #ffffff;
  --text-color: #333333;
}

body.dark-mode {
  --bg-color: #1a1a1a;
  --text-color: #f0f0f0;
}

body {
  background-color: var(--bg-color);
  color: var(--text-color);
}
```

## Advanced Challenges ⭐⭐⭐

### 8. Make a Video Feature

**Goal:** Add a button to create a video from session images.

**Requirements:**
- Install FFmpeg: `sudo apt install ffmpeg`
- Add a "Create Video" button to the gallery
- Use subprocess to run FFmpeg
- Show progress while creating
- Provide download link when done

**FFmpeg command:**
```python
import subprocess

def create_video(session_folder, output_path, fps=30):
    cmd = [
        "ffmpeg", "-y",  # Overwrite output
        "-framerate", str(fps),
        "-pattern_type", "glob",
        "-i", f"{session_folder}/img_*.jpg",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        output_path
    ]
    subprocess.run(cmd, check=True)
```

### 9. Motion Detection Mode

**Goal:** Only capture when motion is detected.

**Concept:**
1. Compare current frame to previous frame
2. If difference is above threshold, capture
3. This saves storage and catches interesting moments

**Algorithm:**
```python
import cv2
import numpy as np

def detect_motion(prev_frame, current_frame, threshold=30):
    """Returns True if motion is detected."""
    # Convert to grayscale
    gray1 = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
    
    # Calculate difference
    diff = cv2.absdiff(gray1, gray2)
    
    # Threshold the difference
    _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
    
    # Count changed pixels
    changed_pixels = np.count_nonzero(thresh)
    total_pixels = thresh.shape[0] * thresh.shape[1]
    change_percent = (changed_pixels / total_pixels) * 100
    
    return change_percent > 1.0  # More than 1% changed
```

### 10. Schedule Feature

**Goal:** Start/stop time-lapses at scheduled times.

**Example use case:**
- Start at 6:00 AM (sunrise)
- Stop at 8:00 PM (sunset)
- Run only on weekdays

**Hints:**
- Use Python's `schedule` library or `APScheduler`
- Add schedule settings to config
- Create a background scheduler thread

### 11. Statistics Dashboard

**Goal:** Add a page showing capture statistics.

**Ideas:**
- Total photos across all sessions
- Photos per hour graph
- Storage usage over time
- Average file size
- Error rate

**Libraries that help:**
- Chart.js (JavaScript) for graphs
- Or generate graphs with Python's matplotlib

### 12. Email Notifications

**Goal:** Get notified when things happen.

**Triggers:**
- Time-lapse completed
- Error occurred
- Storage running low

**Simple email with Python:**
```python
import smtplib
from email.message import EmailMessage

def send_notification(subject, body):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = "pi@example.com"
    msg["To"] = "you@example.com"
    
    # Use your email provider's SMTP settings
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("username", "password")
        server.send_message(msg)
```

### 13. Multi-Camera Support

**Goal:** Capture from multiple cameras simultaneously.

**Challenges:**
- Each camera needs its own thread
- Synchronize captures across cameras
- Organize storage by camera
- Update UI to show multiple feeds

### 14. Live Preview

**Goal:** Show a live video feed from the camera.

**Approach:**
- Stream MJPEG frames to the browser
- Update every second (or faster)
- Show on dashboard before starting capture

**Flask streaming response:**
```python
from flask import Response

@app.route("/video_feed")
def video_feed():
    def generate():
        while True:
            frame = camera.capture()
            _, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   jpeg.tobytes() + b'\r\n')
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
```

## Project Ideas 💡

### Weathercam

Capture weather changes over time:
- Add temperature sensor (DHT22)
- Overlay weather data on images
- Create daily weather summaries

### Plant Growth Tracker

Document plant growth:
- Very long intervals (5-15 minutes)
- Run for weeks or months
- Add measurement overlay

### Security Camera

Use motion detection to:
- Capture only when motion
- Send alerts
- Save only interesting clips

### Art Installation

Create artistic time-lapses:
- Capture a busy area
- Apply filters/effects
- Display on a screen

### Educational Tool

Capture science experiments:
- Mold growing
- Crystals forming
- Ice melting
- Chemical reactions

## Sharing Your Work

### Show Your Time-lapses

- Convert to video with FFmpeg
- Upload to YouTube
- Share on social media
- Enter photography contests

### Contribute to the Project

- Found a bug? Report it on GitHub
- Fixed something? Submit a pull request
- Have an idea? Open a discussion
- Wrote an extension? Share the code

### Teach Others

- Write a blog post about your experience
- Create a tutorial video
- Help others in forums
- Show friends and family

## Resources for Learning More

### Python
- [Automate the Boring Stuff](https://automatetheboringstuff.com/)
- [Real Python](https://realpython.com/)
- [Python Documentation](https://docs.python.org/)

### Raspberry Pi
- [Raspberry Pi Projects](https://projects.raspberrypi.org/)
- [The MagPi Magazine](https://magpi.raspberrypi.com/)
- [Raspberry Pi Forums](https://forums.raspberrypi.com/)

### Photography & Video
- [Time-lapse Guide](https://www.photopills.com/articles/time-lapse-photography-guide)
- [FFmpeg Wiki](https://trac.ffmpeg.org/wiki)
- [OpenCV Tutorials](https://docs.opencv.org/4.x/d9/df8/tutorial_root.html)

### Web Development
- [MDN Web Docs](https://developer.mozilla.org/)
- [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)
- [CSS-Tricks](https://css-tricks.com/)

## Final Words

Remember:
- 🔧 Don't be afraid to break things - you can always fix them
- 📚 Read error messages carefully - they usually tell you what's wrong
- 🔍 Search online - someone has probably had the same problem
- 💬 Ask for help - the programming community is friendly
- 🎉 Have fun - that's what it's all about!

Happy hacking! 🚀

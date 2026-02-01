# 🐛 Troubleshooting Guide

Solutions for common issues on all platforms.

## Quick Diagnosis

| Symptom | Likely Cause | Jump to |
|---------|-------------|---------|
| "Camera not found" | Camera not connected or wrong mode | [Camera Issues](#camera-issues) |
| "Port already in use" | Another app using port 8000 | [Port Issues](#port-issues) |
| "Permission denied" | Missing permissions | [Permission Issues](#permission-issues) |
| "Module not found" | Virtual environment not activated | [Import Errors](#import-errors) |
| Images not saving | Disk full or permission issue | [Storage Issues](#storage-issues) |
| App crashes on start | Configuration error | [Startup Errors](#startup-errors) |

---

## 🪟 Windows Issues

### Virtual Environment Won't Activate

**Symptoms:**

```
venv\Scripts\activate : File cannot be loaded because running scripts is disabled
```

**Solution:**

```powershell
# Allow script execution (run PowerShell as Administrator)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Try activating again
venv\Scripts\activate
```

### Camera Not Found

**Step 1: Check Windows recognizes the camera**

- Open the Windows Camera app
- If it works there, the camera is fine

**Step 2: Test with Python**

```powershell
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera 0:', cap.isOpened()); cap.release()"
```

**Step 3: Try different camera indices**

```powershell
# Try camera index 1, 2, etc.
python -c "import cv2; cap = cv2.VideoCapture(1); print('Camera 1:', cap.isOpened()); cap.release()"
```

**Step 4: Check if another app is using the camera**

- Close Zoom, Teams, Skype, or any video app
- Try again

### Port Already in Use

**Find what's using the port:**

```powershell
netstat -ano | findstr :8000
```

**Solutions:**

1. Close the application using that port
2. Or change the port in `config.yaml`:

   ```yaml
   web_port: 8080
   ```

---

## 🍎 macOS Issues

### Virtual Environment Won't Activate

**Symptoms:**

```
zsh: command not found: python
```

**Solution:**

```bash
# Check which Python you have
which python3

# Create venv with explicit path
/usr/local/bin/python3 -m venv venv

# Or with Homebrew Python
/opt/homebrew/bin/python3 -m venv venv
```

### Camera Permission Denied

**Symptoms:**

- Camera works in FaceTime but not in Python
- No error, but no image captured

**Solution:**

1. Open **System Preferences** (or System Settings)
2. Go to **Security & Privacy** → **Privacy** → **Camera**
3. Enable camera access for:
   - Terminal (or iTerm)
   - Python
4. Restart your terminal application
5. Try again

### Camera Not Found

**Test camera access:**

```bash
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera:', cap.isOpened()); cap.release()"
```

**Try different camera indices:**

```bash
# External cameras often use index 1
python3 -c "import cv2; cap = cv2.VideoCapture(1); print('Camera 1:', cap.isOpened()); cap.release()"
```

### Port Already in Use

**Find what's using the port:**

```bash
lsof -i :8000
```

**Kill the process:**

```bash
# Replace PID with the number from lsof output
kill -9 <PID>
```

**Or change port in config.yaml:**

```yaml
web_port: 8080
```

---

## 🐧 Linux Issues

### Permission Denied (Camera)

**Symptoms:**

```
VIDEOIO ERROR: V4L: can't open camera by index 0
```

**Solution:**

```bash
# Add your user to the video group
sudo usermod -aG video $USER

# Log out and log back in for changes to take effect
# Or reboot
```

### Camera Not Found

**Check for video devices:**

```bash
ls -la /dev/video*
```

**List camera details:**

```bash
v4l2-ctl --list-devices
```

**If no devices found:**

- Check USB connection
- Try different USB port
- Check `lsusb` for USB webcam detection

### Port Already in Use

**Find what's using the port:**

```bash
sudo lsof -i :8000
```

**Kill the process:**

```bash
sudo kill -9 <PID>
```

---

## 🍓 Raspberry Pi Issues

### Pi Camera Not Detected

**Check if camera is recognized:**

```bash
libcamera-hello --list-cameras
```

**If not detected:**

1. **Check ribbon cable connection:**
   - Power off the Pi
   - Reseat the ribbon cable (blue side toward Ethernet port)
   - Make sure clips are secure

2. **Enable camera in config:**

   ```bash
   sudo raspi-config
   ```

   Navigate to: **Interface Options** → **Camera** → **Enable**

3. **Reboot:**

   ```bash
   sudo reboot
   ```

4. **Test again:**

   ```bash
   libcamera-hello
   ```

### USB Webcam Not Working on Pi

**Check if webcam is connected:**

```bash
lsusb
```

**Check for video devices:**

```bash
ls /dev/video*
```

**Test with OpenCV:**

```bash
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera:', cap.isOpened()); cap.release()"
```

### Wrong Camera Mode

**Symptoms:**

- "No camera found" error
- Camera works in terminal but not in app

**Solution:** Check `camera_mode` in config.yaml:

```yaml
# For USB Webcam:
camera_mode: "opencv"

# For Pi Camera Module:
camera_mode: "picamera2"
```

### Service Won't Start

**Check service status:**

```bash
sudo systemctl status pitimelapse
```

**View detailed logs:**

```bash
journalctl -u pitimelapse -n 100
```

**Common fixes:**

- Check the `WorkingDirectory` path in service file
- Make sure virtual environment path is correct
- Verify file permissions

---

## Camera Issues

### Camera Test Script

Create a test script to diagnose camera issues:

```python
# test_camera.py
import cv2

print("Testing cameras...")
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"Camera {i}: Working! Resolution: {frame.shape[1]}x{frame.shape[0]}")
        else:
            print(f"Camera {i}: Opens but can't read")
        cap.release()
    else:
        print(f"Camera {i}: Not available")
```

Run it:

```bash
python test_camera.py
```

### Multiple Cameras Connected

If you have multiple cameras, specify the correct one in code or check which index works.

---

## Port Issues

### Finding Available Ports

**Windows:**

```powershell
netstat -an | findstr "LISTENING"
```

**macOS/Linux:**

```bash
netstat -tuln | grep LISTEN
```

### Recommended Alternative Ports

If 8000 is busy, try:

- `8080` - Common alternative
- `5000` - Flask default
- `3000` - Development servers
- `9000` - Alternative

---

## Permission Issues

### Check File Permissions

**Linux/macOS:**

```bash
# Check ownership of project folder
ls -la

# Fix ownership if needed
sudo chown -R $USER:$USER .
```

### Check Output Directory

```bash
# Make sure data directory exists and is writable
mkdir -p data
chmod 755 data
```

---

## Import Errors

### "ModuleNotFoundError"

**Symptoms:**

```
ModuleNotFoundError: No module named 'flask'
```

**Solution:**

1. Make sure virtual environment is activated:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

2. Reinstall dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### "No module named 'cv2'"

**Solution:**

```bash
pip install opencv-python
```

### Virtual Environment Not Working

**Delete and recreate:**

```bash
# Remove old venv
rm -rf venv  # Linux/macOS
rmdir /s /q venv  # Windows

# Create new venv
python3 -m venv venv

# Activate and install
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

---

## Storage Issues

### Disk Space Check

**Windows:**

```powershell
Get-PSDrive C
```

**macOS/Linux:**

```bash
df -h
```

### Output Directory Issues

**Check if directory exists:**

```bash
ls -la data/
```

**Create if missing:**

```bash
mkdir -p data
```

**Check for write permission:**

```bash
touch data/test_file
rm data/test_file
```

---

## Startup Errors

### Configuration Validation

```bash
python main.py validate
```

This will show any configuration errors.

### Common Config Errors

**Invalid camera_mode:**

```yaml
# Wrong:
camera_mode: picamera

# Correct:
camera_mode: "picamera2"
```

**Invalid YAML syntax:**

- Check for proper indentation (spaces, not tabs)
- Ensure quotes around string values
- No trailing spaces

### Debug Mode

Run with debug output:

```bash
python main.py --debug
```

---

## Network Issues

### Can't Access Web Interface Remotely

1. **Check web_host setting:**

   ```yaml
   web_host: "0.0.0.0"  # Allows remote access
   ```

2. **Check firewall:**

   ```bash
   # Allow port 8000 through firewall
   sudo ufw allow 8000
   ```

3. **Verify Pi's IP address:**

   ```bash
   hostname -I
   ```

### Connection Refused

- Make sure the application is running
- Check you're using the correct IP address
- Verify the port number

---

## Getting More Help

### Check Application Logs

The application prints logs to the console. Look for error messages.

### Run Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest -v
```

### Gather System Information

When reporting issues, include:

```bash
# Python version
python --version

# OS version
uname -a  # Linux/macOS
# or check Windows Settings > System > About

# Installed packages
pip list
```

---

## Next Steps

- [Installation Guide](06_installation_guide.md) - Fresh install
- [Configuration Guide](07_configuration_guide.md) - Settings reference
- [Project Overview](01_project_overview.md) - How it works

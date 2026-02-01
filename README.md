# 🎬 PiTimeLapse Lab

A beginner-friendly Raspberry Pi time-lapse application that captures photos from your Pi camera or USB webcam, saves them with timestamps, and provides a simple web interface to control everything.

**Perfect for:**
- 🌅 Capturing sunsets and sunrises
- 🌱 Watching plants grow
- ☁️ Recording cloud movements
- 🏗️ Documenting projects
- 📚 Learning Python and Raspberry Pi!

## ✨ Features

- 📸 **Capture photos** on a configurable schedule (every X seconds)
- 📷 **Works with** Raspberry Pi Camera Module or any USB webcam
- 🌐 **Web interface** - control everything from your phone or computer
- ⏰ **Timestamp overlay** - burn the date/time into each image
- 📁 **Organized storage** - each session in its own folder
- 📋 **Session logs** - JSON files with all the details
- 🔧 **Easy configuration** - YAML config file with clear comments
- 🛡️ **Resilient** - retries on failures, keeps running
- 📦 **Download sessions** as ZIP files
- 🧪 **Well tested** - includes automated tests

## 🚀 Quick Start

### Prerequisites

- Raspberry Pi (3B+, 4, or 5) with Raspberry Pi OS
- Python 3.10 or newer
- A camera (Pi Camera Module or USB webcam)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/PiTimeLapse-Lab.git
cd PiTimeLapse-Lab

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app!
python main.py
```

### Access the Web Interface

Open a browser and go to: `http://your-pi-ip:8000`

(Replace `your-pi-ip` with your Raspberry Pi's IP address)

## 📖 Complete Setup Guide (From Scratch)

This guide walks you through everything, starting from a brand new Raspberry Pi.

### What You'll Need

**Hardware:**
- Raspberry Pi (Model 3B+, 4, or 5 recommended)
- microSD card (16GB or larger, 32GB recommended)
- Power supply for your Pi
- Camera (choose one):
  - **Option A:** Raspberry Pi Camera Module (best quality)
  - **Option B:** USB Webcam (easiest to set up)
- (Optional) Tripod or camera mount
- (Optional) Case for the Pi

**On Your Windows Computer:**
- Raspberry Pi Imager (free software)
- A microSD card reader

### Step 1: Install Raspberry Pi OS

1. **Download Raspberry Pi Imager**
   - Go to: https://www.raspberrypi.com/software/
   - Click "Download for Windows"
   - Install the downloaded file

2. **Write the OS to your microSD card**
   - Insert your microSD card into your computer
   - Open Raspberry Pi Imager
   - Click "CHOOSE DEVICE" → Select your Pi model
   - Click "CHOOSE OS" → "Raspberry Pi OS (64-bit)"
   - Click "CHOOSE STORAGE" → Select your microSD card
   - Click "NEXT"

3. **Configure settings (important!)**
   - Click "EDIT SETTINGS" when prompted
   - **General tab:**
     - ✅ Set hostname: `raspberrypi` (or choose your own)
     - ✅ Set username and password (remember these!)
     - ✅ Configure wireless LAN (enter your Wi-Fi name and password)
     - ✅ Set locale settings (your timezone)
   - **Services tab:**
     - ✅ Enable SSH
     - Use password authentication
   - Click "SAVE" then "YES" to apply settings
   - Click "YES" to confirm and start writing

4. **Wait for the write to complete** (this takes several minutes)

5. **Eject the card and put it in your Raspberry Pi**

### Step 2: Boot Your Raspberry Pi

1. Insert the microSD card into your Pi
2. Connect the camera (if using Pi Camera):
   - Turn off the Pi
   - Gently insert the ribbon cable into the camera port
   - The blue side should face the Ethernet port
3. Power on your Pi
4. Wait 2-3 minutes for first boot

### Step 3: Find Your Pi's IP Address

**Option A: From your router**
- Log into your router's admin page
- Look for connected devices
- Find "raspberrypi" or similar

**Option B: Using a network scanner**
- Download "Advanced IP Scanner" (Windows)
- Scan your network
- Look for "Raspberry Pi"

**Option C: Using hostname (sometimes works)**
- Try: `raspberrypi.local`

### Step 4: Connect via SSH from Windows

1. **Open Windows Terminal or PowerShell**
   - Press `Win + X`, select "Windows Terminal"
   - Or search for "PowerShell" in the Start menu

2. **Connect to your Pi**
   ```powershell
   ssh pi@YOUR_PI_IP_ADDRESS
   ```
   Replace `YOUR_PI_IP_ADDRESS` with the actual IP (e.g., `192.168.1.100`)
   
   Or if using hostname:
   ```powershell
   ssh pi@raspberrypi.local
   ```

3. **Accept the fingerprint** (type `yes` when prompted)

4. **Enter your password** (the one you set in Raspberry Pi Imager)

You should now see something like:
```
pi@raspberrypi:~ $
```

🎉 You're connected!

### Step 5: Update the System

Run these commands (copy and paste each line):

```bash
# Update package lists
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y git python3-venv python3-pip
```

### Step 6: Install Camera Support

**For Pi Camera Module:**
```bash
# Test if camera is detected
libcamera-hello --list-cameras

# If you see your camera listed, it's working!
# Take a test photo:
libcamera-jpeg -o test.jpg

# Install picamera2 (may already be installed)
sudo apt install -y python3-picamera2
```

**For USB Webcam:**
```bash
# Install required packages
sudo apt install -y libopencv-dev python3-opencv

# Check if webcam is detected
ls /dev/video*
# You should see something like /dev/video0
```

### Step 7: Clone and Install PiTimeLapse Lab

```bash
# Go to home directory
cd ~

# Clone the repository
git clone https://github.com/yourusername/PiTimeLapse-Lab.git

# Enter the directory
cd PiTimeLapse-Lab

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 8: Configure the Application

```bash
# Open the configuration file
nano config.yaml
```

**Key settings to check:**

```yaml
# If using USB Webcam:
camera_mode: "opencv"

# If using Pi Camera:
camera_mode: "picamera2"

# Capture interval (seconds between photos)
interval_seconds: 10

# Web interface settings
web_host: "0.0.0.0"
web_port: 8000
```

Press `Ctrl+O` to save, `Ctrl+X` to exit.

### Step 9: Test the Application

```bash
# Make sure you're in the project directory with venv activated
cd ~/PiTimeLapse-Lab
source venv/bin/activate

# Validate your configuration
python main.py validate

# Start the application
python main.py
```

You should see:
```
==================================================
🎬 PiTimeLapse Lab
==================================================
Camera mode: opencv
Capture interval: 10 seconds
Output directory: ./data
Web interface: http://0.0.0.0:8000
==================================================
Press Ctrl+C to stop the server
```

### Step 10: Access the Web Interface

From your computer or phone, open a browser and go to:

```
http://YOUR_PI_IP:8000
```

For example: `http://192.168.1.100:8000`

You should see the PiTimeLapse Lab dashboard!

### Step 11: Start Your First Time-lapse!

1. Click the big green "▶️ Start Time-lapse" button
2. Watch the photo count increase
3. Check the Gallery to see your images
4. Click "⏹️ Stop Time-lapse" when done

🎉 Congratulations! You've created your first time-lapse!

### Step 12: Run Automatically on Boot (Optional)

To have PiTimeLapse Lab start automatically when your Pi boots:

```bash
# Create a systemd service file
sudo nano /etc/systemd/system/pitimelapse.service
```

Paste this content:
```ini
[Unit]
Description=PiTimeLapse Lab
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PiTimeLapse-Lab
ExecStart=/home/pi/PiTimeLapse-Lab/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit, then enable the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable pitimelapse

# Start it now
sudo systemctl start pitimelapse

# Check status
sudo systemctl status pitimelapse
```

## 🔧 Configuration

Edit `config.yaml` to customize the application:

```yaml
# Camera Settings
camera_mode: "opencv"      # "opencv" for webcam, "picamera2" for Pi camera
resolution_width: 1280     # Image width in pixels
resolution_height: 720     # Image height in pixels

# Capture Settings
interval_seconds: 10       # Seconds between captures
start_delay_seconds: 0     # Wait before first capture
duration_limit_seconds: 0  # 0 = run until stopped

# Output Settings
output_dir: "./data"       # Where to save images
image_format: "jpg"        # "jpg" or "png"
overlay_timestamp: true    # Add timestamp to images

# Web Server
web_host: "0.0.0.0"        # Accept connections from any IP
web_port: 8000             # Port number
```

## 🖥️ CLI Commands

```bash
# Start the web server (default)
python main.py

# Start with debug mode (auto-reload on code changes)
python main.py --debug

# Validate your configuration
python main.py validate

# List all sessions
python main.py sessions

# Delete sessions older than 7 days
python main.py cleanup --days 7

# Create a default config file
python main.py init
```

## 📡 API Endpoints

The web interface uses these REST API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | Get current capture status |
| POST | `/api/start` | Start a new time-lapse |
| POST | `/api/stop` | Stop current time-lapse |
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/<id>` | Get session details |
| GET | `/api/sessions/<id>/latest-images` | Get recent images |
| GET | `/api/config` | Get current configuration |
| GET | `/api/storage` | Get storage usage info |

## 🐛 Troubleshooting

### Camera Not Found

**USB Webcam:**
```bash
# Check if webcam is connected
lsusb

# Check for video devices
ls /dev/video*

# If nothing shows, try different USB port
```

**Pi Camera:**
```bash
# Check if camera is detected
libcamera-hello --list-cameras

# If not detected:
# 1. Check ribbon cable connection
# 2. Reseat the cable (blue side toward Ethernet)
# 3. Run: sudo raspi-config
#    → Interface Options → Camera → Enable
# 4. Reboot
```

### Permission Denied

```bash
# Add your user to the video group
sudo usermod -aG video $USER

# Log out and back in for changes to take effect
```

### Port Already in Use

```bash
# Check what's using port 8000
sudo lsof -i :8000

# Either stop that process or change web_port in config.yaml
```

### Images Not Saving

```bash
# Check disk space
df -h

# Make sure the output directory exists and is writable
ls -la ./data
```

### Application Crashes

```bash
# Check the logs
journalctl -u pitimelapse -n 50

# Run manually to see errors
python main.py
```

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=src/pitimelapse

# Run specific test file
pytest tests/test_config.py -v
```

## 📚 Documentation

Check out the `docs/` folder for learning materials:

- [01 - Project Overview](docs/01_project_overview.md) - How everything fits together
- [02 - Python Basics](docs/02_python_basics_used.md) - Python concepts we use
- [03 - Web Basics with Flask](docs/03_web_basics_flask.md) - How the web interface works
- [04 - Hardware & Camera Basics](docs/04_hardware_camera_basics.md) - Camera and Pi hardware
- [05 - Extensions & Challenges](docs/05_extensions_challenges.md) - Ideas to extend the project!

## 🔒 Safety & Privacy

**Important considerations when using cameras:**

- ⚠️ Only record in places where you have permission
- 🏠 Be mindful of neighbors and their privacy
- 📋 Check local laws about recording in public spaces
- 🔐 Secure your Pi (change default password!)
- 🌐 Don't expose the web interface to the internet without protection

## 🤝 Contributing

Contributions are welcome! Here's how:

1. Fork the repository
2. Create a feature branch: `git checkout -b my-new-feature`
3. Make your changes
4. Run tests: `pytest`
5. Commit: `git commit -am 'Add some feature'`
6. Push: `git push origin my-new-feature`
7. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- The Raspberry Pi Foundation for amazing hardware
- The Flask team for a great web framework
- The OpenCV team for computer vision tools
- Everyone who contributed to picamera2

---

Made with ❤️ for makers, learners, and time-lapse enthusiasts!

**Questions?** Open an issue on GitHub.

**Found a bug?** Report it! We appreciate your feedback.

**Built something cool?** Share it with us!

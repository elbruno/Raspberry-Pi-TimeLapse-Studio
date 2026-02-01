# 🔧 Installation Guide

Complete installation instructions for all supported platforms. Choose your operating system below.

## Prerequisites (All Platforms)

- **Python 3.10 or newer**
- **Git** (for cloning the repository)
- A camera (Pi Camera Module, USB webcam, or built-in laptop camera)

---

## 🪟 Windows Installation

### Step 1: Install Python

1. Visit <https://www.python.org/downloads/>
2. Download the latest Python 3.10+ for Windows
3. **Important:** Check ✅ "Add Python to PATH" during installation
4. Open PowerShell or Command Prompt to verify:

   ```powershell
   python --version
   ```

### Step 2: Install Git

1. Visit <https://git-scm.com/>
2. Download and install Git for Windows
3. Verify installation:

   ```powershell
   git --version
   ```

### Step 3: Clone and Install

```powershell
# Open PowerShell or Command Prompt

# Clone the repository
git clone https://github.com/yourusername/PiTimeLapse-Lab.git
cd PiTimeLapse-Lab

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Configure the Application

```powershell
# Edit the configuration file (opens in your default text editor)
notepad config.yaml
```

For USB webcam (most Windows users), ensure:

```yaml
camera_mode: "opencv"
web_host: "127.0.0.1"  # or "0.0.0.0" for network access
web_port: 8000
```

Save and close.

### Step 5: Run the Application

```powershell
# Make sure venv is activated
venv\Scripts\activate

# Start the app
python main.py
```

You should see:

```
==================================================
🎬 PiTimeLapse Lab
==================================================
Camera mode: opencv
Web interface: http://127.0.0.1:8000
==================================================
Press Ctrl+C to stop the server
```

### Step 6: Access the Web Interface

Open your browser and go to: `http://localhost:8000`

---

## 🍎 macOS Installation

### Step 1: Install Python

**Option A: Using Homebrew (recommended)**

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and Git
brew install python@3.11 git
```

**Option B: Direct Download**

Download from <https://www.python.org/>

### Step 2: Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/PiTimeLapse-Lab.git
cd PiTimeLapse-Lab

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure the Application

```bash
# Edit the configuration file
nano config.yaml
```

For USB webcam or built-in camera, ensure:

```yaml
camera_mode: "opencv"
web_host: "127.0.0.1"  # or "0.0.0.0" for network access
web_port: 8000
```

Press `Ctrl+O` to save, `Ctrl+X` to exit.

### Step 4: Run the Application

```bash
# Make sure venv is activated
source venv/bin/activate

# Start the app
python main.py
```

You should see:

```
==================================================
🎬 PiTimeLapse Lab
==================================================
Camera mode: opencv
Web interface: http://127.0.0.1:8000
==================================================
Press Ctrl+C to stop the server
```

### Step 5: Access the Web Interface

Open your browser and go to: `http://localhost:8000`

---

## 🐧 Linux Installation

### Step 1: Install Dependencies

```bash
# Update package lists
sudo apt update

# Install Python, Git and virtual environment support
sudo apt install -y python3 python3-venv python3-pip git

# For USB webcams, install OpenCV dependencies
sudo apt install -y libopencv-dev python3-opencv
```

### Step 2: Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/PiTimeLapse-Lab.git
cd PiTimeLapse-Lab

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure the Application

```bash
# Edit the configuration file
nano config.yaml
```

Set your preferred options:

```yaml
camera_mode: "opencv"
web_host: "0.0.0.0"  # Allow network access
web_port: 8000
```

Press `Ctrl+O` to save, `Ctrl+X` to exit.

### Step 4: Run the Application

```bash
source venv/bin/activate
python main.py
```

---

## 🍓 Raspberry Pi Installation (Complete Guide)

This is a complete step-by-step guide starting from a brand new Raspberry Pi.

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

**On Your Computer:**

- Raspberry Pi Imager (free software)
- A microSD card reader

### Step 1: Install Raspberry Pi OS

1. **Download Raspberry Pi Imager**
   - Go to: <https://www.raspberrypi.com/software/>
   - Download for your OS (Windows/macOS/Linux)
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

- Download "Advanced IP Scanner" (Windows) or use `arp -a` (macOS/Linux)
- Scan your network
- Look for "Raspberry Pi"

**Option C: Using hostname (sometimes works)**

- Try: `raspberrypi.local`

### Step 4: Connect via SSH

**From Windows (PowerShell):**

```powershell
ssh pi@YOUR_PI_IP_ADDRESS
```

**From macOS/Linux (Terminal):**

```bash
ssh pi@YOUR_PI_IP_ADDRESS
```

Replace `YOUR_PI_IP_ADDRESS` with the actual IP (e.g., `192.168.1.100`)

Accept the fingerprint (type `yes`), then enter your password.

### Step 5: Update the System

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

# If you get PEP 668 errors about externally-managed environments, use:
pip install --break-system-packages -r requirements.txt
```

**Important:** If the last command fails due to a "externally-managed-environment" error, use the `--break-system-packages` flag. This is safe for development environments and is necessary on some Raspberry Pi OS versions.

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

### Step 11: Start Your First Time-lapse

1. Click the big green "▶️ Start Time-lapse" button
2. Watch the photo count increase
3. Check the Gallery to see your images
4. Click "⏹️ Stop Time-lapse" when done

🎉 Congratulations! You've created your first time-lapse!

---

## 🔄 Run Automatically on Boot (Raspberry Pi)

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

---

## Next Steps

- [Configuration Guide](07_configuration_guide.md) - Customize all settings
- [Troubleshooting](08_troubleshooting.md) - Fix common issues
- [Project Overview](01_project_overview.md) - Understand how it works

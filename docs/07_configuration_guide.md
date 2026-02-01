# ⚙️ Configuration Guide

Complete guide to configuring PiTimeLapse Lab. All settings are in `config.yaml`.

## Quick Reference

```yaml
# Camera Settings
camera_mode: "opencv"        # "opencv" or "picamera2"
resolution_width: 1280       # Image width in pixels
resolution_height: 720       # Image height in pixels

# Capture Settings
interval_seconds: 10         # Seconds between captures
start_delay_seconds: 0       # Wait before first capture
duration_limit_seconds: 0    # 0 = run until stopped

# Output Settings
output_dir: "./data"         # Where to save images
image_format: "jpg"          # "jpg" or "png"
overlay_timestamp: true      # Add timestamp to images

# Web Server
web_host: "127.0.0.1"        # "127.0.0.1" or "0.0.0.0"
web_port: 8000               # Port number
```

---

## Camera Settings

### `camera_mode`

Selects which camera driver to use.

| Value | Description | Platforms |
|-------|-------------|-----------|
| `"opencv"` | OpenCV driver for USB/built-in cameras | Windows, macOS, Linux, Pi |
| `"picamera2"` | Native Pi Camera driver | Raspberry Pi only |

**When to use each:**

- **`opencv`** (RECOMMENDED default) - Use for:
  - USB webcams on any platform
  - Built-in laptop cameras (Windows/macOS/Linux)
  - Built-in cameras on Raspberry Pi
  - Cross-platform compatibility and easy setup
  - Works with most camera hardware

- **`picamera2`** (Advanced, Raspberry Pi only) - Use for:
  - Raspberry Pi Camera Module (CSI/ribbon cable camera)
  - Maximum performance on official Pi cameras
  - Requires picamera2 library to be installed

### `resolution_width` / `resolution_height`

The size of captured images in pixels.

| Resolution | Pixels | File Size (JPG) | Use Case |
|------------|--------|-----------------|----------|
| 640×480 | 307K | ~50 KB | Low storage, fast capture |
| 1280×720 | 921K | ~150 KB | Good balance (default) |
| 1920×1080 | 2.1M | ~300 KB | Full HD quality |
| 3840×2160 | 8.3M | ~1 MB | 4K (high storage) |

**Trade-offs:**

- Higher resolution = Better quality, larger files, more processing
- Lower resolution = Smaller files, faster capture, less storage

**Example:**

```yaml
resolution_width: 1920
resolution_height: 1080
```

---

## Capture Settings

### `interval_seconds`

Time between photo captures.

| Value | Use Case |
|-------|----------|
| 1-5 | Fast-moving clouds, traffic |
| 10-30 | Sunsets, general time-lapses |
| 60-300 | Slow changes, plant growth |
| 600+ | Very slow processes (construction) |

**Storage calculation:**

```
Photos per hour = 3600 / interval_seconds

Example: 10-second interval
- Photos per hour: 360
- Photos per day: 8,640
- At 150 KB each: 1.3 GB per day
```

### `start_delay_seconds`

Wait time before the first capture after pressing Start.

- `0` - Start immediately (default)
- `10` - Wait 10 seconds (time to get in position)
- `60` - Wait 1 minute

### `duration_limit_seconds`

Automatically stop after this many seconds.

- `0` - Run until manually stopped (default)
- `3600` - Stop after 1 hour
- `86400` - Stop after 24 hours

---

## Output Settings

### `output_dir`

Where captured images are saved.

```yaml
output_dir: "./data"           # Relative to project folder
output_dir: "/home/pi/photos"  # Absolute path
output_dir: "D:/timelapse"     # Windows absolute path
```

**Structure:**

```
data/
├── session_20240115_143022/
│   ├── session.json           # Session metadata
│   ├── img_0001_143022.jpg
│   ├── img_0002_143032.jpg
│   └── ...
└── session_20240116_091500/
    └── ...
```

### `image_format`

| Format | Compression | Quality | File Size | Use Case |
|--------|-------------|---------|-----------|----------|
| `"jpg"` | Lossy | Good | Smaller | Most time-lapses |
| `"png"` | Lossless | Perfect | 3-5x larger | When quality is critical |

### `overlay_timestamp`

Burns date/time into each image.

- `true` - Add timestamp overlay (default)
- `false` - Clean images without text

**Example overlay:**

```
┌─────────────────────────────────────────┐
│                                         │
│                                         │
│                                         │
│                                         │
│  2024-01-15 14:30:22                    │
└─────────────────────────────────────────┘
```

---

## Web Server Settings

### `web_host`

Controls which network interfaces accept connections.

| Value | Access | Security | Use Case |
|-------|--------|----------|----------|
| `"127.0.0.1"` | Same machine only | Safer | Development, testing |
| `"0.0.0.0"` | Any network interface | Less secure | Raspberry Pi, remote access |

**When to use each:**

- **`127.0.0.1`** (localhost only)
  - Can only access from the same computer
  - Recommended for Windows/macOS development
  - More secure

- **`0.0.0.0`** (all interfaces)
  - Can access from other devices on your network
  - Required for Raspberry Pi setups
  - Access via `http://pi-ip-address:8000`

### `web_port`

The port number for the web interface.

```yaml
web_port: 8000    # Default
web_port: 8080    # Alternative if 8000 is busy
web_port: 5000    # Flask default
```

**Note:** Ports below 1024 require root/admin privileges.

---

## Platform-Specific Recommendations

### Windows

```yaml
camera_mode: "opencv"
web_host: "127.0.0.1"
output_dir: "./data"
```

### macOS

```yaml
camera_mode: "opencv"
web_host: "127.0.0.1"
output_dir: "./data"
```

### Raspberry Pi (USB Webcam)

```yaml
camera_mode: "opencv"
web_host: "0.0.0.0"
output_dir: "./data"
```

### Raspberry Pi (Pi Camera)

```yaml
camera_mode: "picamera2"
web_host: "0.0.0.0"
output_dir: "./data"
```

---

## Editing the Configuration

### Windows

```powershell
notepad config.yaml
```

### macOS / Linux

```bash
nano config.yaml
# or
vim config.yaml
```

### Validate Configuration

After editing, validate your changes:

```bash
python main.py validate
```

This checks for errors before starting.

---

## Environment Variables

You can override config values with environment variables:

```bash
# Linux/macOS
export PITIMELAPSE_PORT=8080
python main.py

# Windows PowerShell
$env:PITIMELAPSE_PORT = "8080"
python main.py
```

---

## Example Configurations

### Quick Test (Fast Capture)

```yaml
camera_mode: "opencv"
resolution_width: 640
resolution_height: 480
interval_seconds: 2
image_format: "jpg"
overlay_timestamp: true
web_host: "127.0.0.1"
web_port: 8000
```

### Sunset Time-lapse

```yaml
camera_mode: "opencv"
resolution_width: 1920
resolution_height: 1080
interval_seconds: 10
duration_limit_seconds: 7200  # 2 hours
image_format: "jpg"
overlay_timestamp: true
```

### Plant Growth (Long-term)

```yaml
camera_mode: "picamera2"
resolution_width: 1280
resolution_height: 720
interval_seconds: 300  # Every 5 minutes
duration_limit_seconds: 0  # Run continuously
image_format: "jpg"
overlay_timestamp: true
```

### High Quality (4K)

```yaml
camera_mode: "picamera2"
resolution_width: 3840
resolution_height: 2160
interval_seconds: 30
image_format: "png"  # Lossless
overlay_timestamp: false  # Clean images
```

---

## Next Steps

- [Installation Guide](06_installation_guide.md) - Platform setup
- [Troubleshooting](08_troubleshooting.md) - Fix common issues
- [CLI & API Reference](09_cli_api_reference.md) - Commands and endpoints

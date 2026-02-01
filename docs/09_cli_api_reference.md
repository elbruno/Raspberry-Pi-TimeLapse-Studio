# 📡 CLI & API Reference

Command-line interface and REST API documentation for PiTimeLapse Lab.

---

## 🖥️ Command Line Interface

### Basic Usage

```bash
python main.py [command] [options]
```

### Commands

#### `python main.py` (default)

Start the web server.

```bash
# Start with default settings
python main.py

# Start with debug mode (auto-reload on code changes)
python main.py --debug
```

#### `python main.py validate`

Validate configuration file without starting the server.

```bash
python main.py validate
```

**Output examples:**

```
✅ Configuration is valid
```

```
❌ Configuration errors:
  - interval_seconds must be at least 1
  - Invalid camera_mode: webcam
```

#### `python main.py sessions`

List all capture sessions.

```bash
python main.py sessions
```

**Output:**

```
Sessions:
  session_20240115_143022: 42 photos, 2024-01-15 14:30:22
  session_20240116_091500: 128 photos, 2024-01-16 09:15:00
```

#### `python main.py cleanup`

Delete old sessions to free space.

```bash
# Delete sessions older than 7 days
python main.py cleanup --days 7

# Preview what would be deleted (dry run)
python main.py cleanup --days 7 --dry-run
```

#### `python main.py init`

Create a default configuration file.

```bash
python main.py init
```

Creates `config.yaml` if it doesn't exist.

### Options

| Option | Description |
|--------|-------------|
| `--debug` | Enable debug mode with auto-reload |
| `--config FILE` | Use a specific config file |
| `--port PORT` | Override web server port |

### Examples

```bash
# Start on a different port
python main.py --port 8080

# Use a custom config file
python main.py --config my_config.yaml

# Debug mode for development
python main.py --debug
```

---

## 📡 REST API

The web interface communicates with the backend using these REST endpoints.

### Base URL

```
http://localhost:8000/api
```

Or for Raspberry Pi:

```
http://YOUR_PI_IP:8000/api
```

---

### Status Endpoints

#### GET `/api/status`

Get current capture status.

**Response:**

```json
{
  "is_running": true,
  "current_session_id": "session_20240115_143022",
  "total_photos": 42,
  "last_capture_time": "2024-01-15T14:35:22",
  "uptime_seconds": 322,
  "next_capture_in": 8
}
```

**Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `is_running` | boolean | Whether capture is active |
| `current_session_id` | string | Current session ID (null if not running) |
| `total_photos` | integer | Photos captured in current session |
| `last_capture_time` | string | ISO timestamp of last capture |
| `uptime_seconds` | number | Seconds since session started |
| `next_capture_in` | number | Seconds until next capture |

---

### Control Endpoints

#### POST `/api/start`

Start a new time-lapse session.

**Request:** No body required

**Response (success):**

```json
{
  "success": true,
  "message": "Time-lapse started",
  "session_id": "session_20240115_143022"
}
```

**Response (error):**

```json
{
  "success": false,
  "message": "Time-lapse is already running"
}
```

#### POST `/api/stop`

Stop the current time-lapse session.

**Request:** No body required

**Response (success):**

```json
{
  "success": true,
  "message": "Time-lapse stopped",
  "total_photos": 42
}
```

**Response (error):**

```json
{
  "success": false,
  "message": "No time-lapse is running"
}
```

---

### Session Endpoints

#### GET `/api/sessions`

List all capture sessions.

**Response:**

```json
{
  "sessions": [
    {
      "id": "session_20240115_143022",
      "start_time": "2024-01-15T14:30:22",
      "end_time": "2024-01-15T16:45:33",
      "total_photos": 800,
      "interval_seconds": 10
    },
    {
      "id": "session_20240116_091500",
      "start_time": "2024-01-16T09:15:00",
      "end_time": null,
      "total_photos": 128,
      "interval_seconds": 10
    }
  ]
}
```

#### GET `/api/sessions/<id>`

Get details for a specific session.

**URL Parameters:**

- `id` - Session ID (e.g., `session_20240115_143022`)

**Response:**

```json
{
  "id": "session_20240115_143022",
  "start_time": "2024-01-15T14:30:22",
  "end_time": "2024-01-15T16:45:33",
  "total_photos": 800,
  "interval_seconds": 10,
  "camera_mode": "opencv",
  "resolution": "1280x720"
}
```

#### GET `/api/sessions/<id>/latest-images`

Get the most recent images from a session.

**URL Parameters:**

- `id` - Session ID

**Query Parameters:**

- `count` - Number of images to return (default: 10, max: 50)

**Response:**

```json
{
  "images": [
    {
      "filename": "img_0042_163522.jpg",
      "timestamp": "2024-01-15T16:35:22",
      "url": "/data/session_20240115_143022/img_0042_163522.jpg"
    },
    {
      "filename": "img_0041_163512.jpg",
      "timestamp": "2024-01-15T16:35:12",
      "url": "/data/session_20240115_143022/img_0041_163512.jpg"
    }
  ]
}
```

#### GET `/api/sessions/<id>/download`

Download session as a ZIP file.

**URL Parameters:**

- `id` - Session ID

**Response:** ZIP file download

---

### Configuration Endpoints

#### GET `/api/config`

Get current configuration.

**Response:**

```json
{
  "camera_mode": "opencv",
  "resolution_width": 1280,
  "resolution_height": 720,
  "interval_seconds": 10,
  "image_format": "jpg",
  "overlay_timestamp": true,
  "web_host": "0.0.0.0",
  "web_port": 8000
}
```

#### POST `/api/config`

Update configuration (requires restart).

**Request:**

```json
{
  "interval_seconds": 15,
  "resolution_width": 1920,
  "resolution_height": 1080
}
```

**Response:**

```json
{
  "success": true,
  "message": "Configuration updated. Restart required."
}
```

---

### Storage Endpoints

#### GET `/api/storage`

Get storage usage information.

**Response:**

```json
{
  "total_bytes": 32000000000,
  "used_bytes": 12500000000,
  "free_bytes": 19500000000,
  "sessions_count": 5,
  "total_photos": 2500,
  "usage_percent": 39.1
}
```

---

## Using the API

### With cURL

```bash
# Get status
curl http://localhost:8000/api/status

# Start time-lapse
curl -X POST http://localhost:8000/api/start

# Stop time-lapse
curl -X POST http://localhost:8000/api/stop

# List sessions
curl http://localhost:8000/api/sessions
```

### With Python

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Get status
response = requests.get(f"{BASE_URL}/status")
status = response.json()
print(f"Running: {status['is_running']}")

# Start time-lapse
response = requests.post(f"{BASE_URL}/start")
result = response.json()
print(result['message'])

# Stop time-lapse
response = requests.post(f"{BASE_URL}/stop")
result = response.json()
print(f"Captured {result.get('total_photos', 0)} photos")
```

### With JavaScript

```javascript
// Get status
fetch('/api/status')
  .then(response => response.json())
  .then(data => {
    console.log('Running:', data.is_running);
    console.log('Photos:', data.total_photos);
  });

// Start time-lapse
fetch('/api/start', { method: 'POST' })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('Started session:', data.session_id);
    } else {
      console.error('Error:', data.message);
    }
  });
```

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid parameters) |
| 404 | Not found (session doesn't exist) |
| 409 | Conflict (e.g., already running) |
| 500 | Server error |

---

## Next Steps

- [Configuration Guide](07_configuration_guide.md) - All settings explained
- [Troubleshooting](08_troubleshooting.md) - Fix common issues
- [Extensions & Challenges](05_extensions_challenges.md) - Build on top of the API

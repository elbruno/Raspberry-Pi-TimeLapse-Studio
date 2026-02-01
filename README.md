# 🎬 PiTimeLapse Lab

A beginner-friendly time-lapse application that works on **Windows**, **macOS**, **Linux**, and **Raspberry Pi**! 📸

Capture photos from your Pi camera, USB webcam, or built-in laptop camera. Save them with timestamps and control everything through a simple web interface.

**Perfect for:**

- 🌅 Capturing sunsets and sunrises
- 🌱 Watching plants grow
- ☁️ Recording cloud movements
- 🏗️ Documenting projects
- 📚 Learning Python and Raspberry Pi!

## ✨ Features

- 📸 **Capture photos** on a configurable schedule
- 📷 **Works with** Pi Camera, USB webcam, or laptop camera
- 💻 **Cross-platform:** Windows, macOS, Linux, Raspberry Pi
- 🌐 **Web interface** - control from your phone or computer
- ⏰ **Timestamp overlay** on images
- 📦 **Download sessions** as ZIP files
- 🧪 **Well tested** with automated tests

---

## 🚀 Quick Start

### 1. Clone & Install

**Windows:**

```powershell
git clone https://github.com/yourusername/PiTimeLapse-Lab.git
cd PiTimeLapse-Lab
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux / Raspberry Pi:**

```bash
git clone https://github.com/yourusername/PiTimeLapse-Lab.git
cd PiTimeLapse-Lab
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run

```bash
python main.py
```

### 3. Open Browser

Go to `http://localhost:8000` and start your first time-lapse!

---

## 📖 Where to Go Next

Choose based on what you need:

| I want to... | Go to... |
|--------------|----------|
| 🔧 **Set up from scratch** | [Installation Guide](docs/06_installation_guide.md) |
| ⚙️ **Configure settings** | [Configuration Guide](docs/07_configuration_guide.md) |
| 🐛 **Fix a problem** | [Troubleshooting](docs/08_troubleshooting.md) |
| 📡 **Use the API** | [CLI & API Reference](docs/09_cli_api_reference.md) |
| 📚 **Understand the code** | [Project Overview](docs/01_project_overview.md) |
| 🐍 **Learn Python basics** | [Python Basics](docs/02_python_basics_used.md) |
| 🌐 **Learn web/Flask** | [Web Basics](docs/03_web_basics_flask.md) |
| 📷 **Learn about cameras** | [Hardware & Camera](docs/04_hardware_camera_basics.md) |
| 🚀 **Extend the project** | [Extensions & Challenges](docs/05_extensions_challenges.md) |

---

## 🔧 Basic Configuration

Edit `config.yaml`:

```yaml
camera_mode: "opencv"      # Use "picamera2" for Pi Camera
interval_seconds: 10       # Seconds between photos
web_host: "127.0.0.1"      # Use "0.0.0.0" for network access
web_port: 8000
```

📖 See [Configuration Guide](docs/07_configuration_guide.md) for all options.

---

## 🖥️ CLI Commands

```bash
python main.py              # Start web server
python main.py validate     # Check configuration
python main.py sessions     # List all sessions
python main.py --debug      # Debug mode
```

📖 See [CLI & API Reference](docs/09_cli_api_reference.md) for full details.

---

## 🔒 Safety & Privacy

- ⚠️ Only record where you have permission
- 🔐 Secure your Pi (change default password!)
- 🌐 Don't expose to the internet without protection

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b my-new-feature`
3. Make your changes and run tests: `pytest`
4. Submit a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

Made with ❤️ for makers, learners, and time-lapse enthusiasts!

**Questions?** Open an issue · **Found a bug?** Report it! · **Built something cool?** Share it!

# 🎬 PiTimeLapse Lab

A beginner-friendly time-lapse application that works on **Windows**, **macOS**, **Linux**, and **Raspberry Pi**! 📸

Capture photos using USB webcams (recommended default), built-in laptop cameras, or Raspberry Pi cameras. Save them with timestamps and control everything through a simple web interface.

**Perfect for:**

- 🌅 Capturing sunsets and sunrises
- 🌱 Watching plants grow
- ☁️ Recording cloud movements
- 🏗️ Documenting projects
- 📚 Learning Python and Raspberry Pi!

---

## 🎓 New to Programming? Start Here

This project is designed for **beginners**! If you're new to programming or Raspberry Pi:

1. **Start simple**: Try `simple.py` first - it's just 80 lines of code!
2. **Learn the concepts**: Check out [Python Basics](docs/02_python_basics_used.md)
3. **Don't worry about mistakes**: They're the best way to learn!

<details>
<summary><strong>📖 Beginner's Glossary - Click to expand!</strong></summary>

| Term | What it means |
|------|--------------|
| **Repository (repo)** | A folder containing all the project files, tracked by Git |
| **Clone** | Download a copy of a repository to your computer |
| **Terminal/Command Line** | A text interface to type commands (like PowerShell or Bash) |
| **Virtual Environment (venv)** | A private space for this project's Python packages, so they don't conflict with other projects |
| **pip** | Python's package installer - downloads and installs Python libraries |
| **requirements.txt** | A list of Python packages this project needs |
| **Port** | A number that identifies where a program "listens" for connections (like 8000) |
| **localhost** | Your own computer - used to access web apps running on your machine |
| **Camera index** | A number identifying which camera to use (0 = first camera, 1 = second, etc.) |
| **OpenCV** | A popular library for working with cameras and images |
| **Flask** | A simple framework for building web applications in Python |

</details>

---

## ✨ Features

- 📸 **Capture photos** on a configurable schedule
- 📷 **Works with** USB webcams (recommended), built-in cameras, or Pi Camera Module
- 💻 **Cross-platform:** Windows, macOS, Linux, Raspberry Pi
- 🌐 **Web interface** - control from your phone or computer
- ⏰ **Timestamp overlay** on images
- 📦 **Download sessions** as ZIP files
- 🧪 **Well tested** with automated tests

---

## � Screenshots

| Dashboard | Gallery | Settings |
|-----------|---------|----------|
| ![Dashboard](01%20-%20WebApp%20TimeLapse/images/01_dashboard.jpeg) | ![Gallery](01%20-%20WebApp%20TimeLapse/images/02_gallery.jpeg) | ![Settings](01%20-%20WebApp%20TimeLapse/images/03_settings.jpeg) |

---

## 🚀 Quick Start

### 💡 What You'll Be Doing

These commands will:

1. **Clone**: Download a copy of this project to your computer
2. **Create a virtual environment**: Set up an isolated Python workspace
3. **Install dependencies**: Download the Python packages this project needs
4. **Run the app**: Start the web interface!

### 1. Clone & Install

**Windows:**

```powershell
# Download the project (creates a new folder)
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git

# Go into the scenario 01 folder
cd "Raspberry-Pi-TimeLapse-Studio\01 - WebApp TimeLapse"

# Create a virtual environment (a private Python workspace)
python -m venv venv

# Activate it (you'll see "(venv)" in your prompt)
venv\Scripts\activate

# Install the required Python packages
pip install -r requirements.txt
```

**macOS / Linux / Raspberry Pi:**

```bash
# Download the project (creates a new folder)
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git

# Go into the scenario 01 folder
cd "Raspberry-Pi-TimeLapse-Studio/01 - WebApp TimeLapse"

# Create a virtual environment
python3 -m venv venv

# Activate it (you'll see "(venv)" in your prompt)
source venv/bin/activate

# Install the required Python packages
pip install -r requirements.txt
```

> 💡 **What happens if you skip the virtual environment?** The app will still work, but you might get conflicts with other Python projects on your computer. Virtual environments keep things organized!

### 2. Validate Your Setup

Before running, verify everything is configured correctly:

```bash
python main.py validate
```

This checks:

- ✅ Configuration file
- ✅ Required packages
- ✅ Camera availability
- ✅ Directory permissions

If it shows any errors, the troubleshooting guide will help!

### 3. Run

```bash
python main.py
```

### 4. Open Browser

Go to `http://localhost:8000` and start your first time-lapse!

> 💡 **What does `localhost:8000` mean?** "localhost" is your own computer, and "8000" is the port number where the app is listening. It's like an address and apartment number!

---

## 🔄 Returning Users

Already set up? Just activate your environment and run:

**Windows:**

```powershell
cd "Raspberry-Pi-TimeLapse-Studio\01 - WebApp TimeLapse"
venv\Scripts\activate
python main.py validate     # Optional: check configuration
python main.py
```

**macOS / Linux / Raspberry Pi:**

```bash
cd "Raspberry-Pi-TimeLapse-Studio/01 - WebApp TimeLapse"
source venv/bin/activate
python main.py validate     # Optional: check configuration
python main.py
```

---

## 📖 Where to Go Next

Choose based on what you need:

| I want to... | Go to... |
|--------------|----------|
| 🎯 **Start learning (beginner)** | [Simple Script Guide](01%20-%20WebApp%20TimeLapse/docs/10_simple_script_guide.md) ⬅️ Start here! |
| 🔧 **Set up from scratch** | [Installation Guide](01%20-%20WebApp%20TimeLapse/docs/06_installation_guide.md) |
| ⚙️ **Configure settings** | [Configuration Guide](01%20-%20WebApp%20TimeLapse/docs/07_configuration_guide.md) |
| 🐛 **Fix a problem** | [Troubleshooting](01%20-%20WebApp%20TimeLapse/docs/08_troubleshooting.md) |
| 📡 **Use the API** | [CLI & API Reference](01%20-%20WebApp%20TimeLapse/docs/09_cli_api_reference.md) |
| 📚 **Understand the code** | [Project Overview](01%20-%20WebApp%20TimeLapse/docs/01_project_overview.md) |
| 🐍 **Learn Python basics** | [Python Basics](01%20-%20WebApp%20TimeLapse/docs/02_python_basics_used.md) |
| 🌐 **Learn web/Flask** | [Web Basics](01%20-%20WebApp%20TimeLapse/docs/03_web_basics_flask.md) |
| 📷 **Learn about cameras** | [Hardware & Camera](01%20-%20WebApp%20TimeLapse/docs/04_hardware_camera_basics.md) |
| 🚀 **Extend the project** | [Extensions & Challenges](01%20-%20WebApp%20TimeLapse/docs/05_extensions_challenges.md) |

---

## 🔧 Basic Configuration

Edit `config.yaml`:

```yaml
camera_mode: opencv          # Recommended default (USB/built-in cameras)
camera_index: 0              # 0 = first camera, 1 = second, etc.
interval_seconds: 10         # Seconds between photos
output_dir: ./data           # Where photos are saved
web_host: 0.0.0.0            # 0.0.0.0 = accessible from network, 127.0.0.1 = local only
web_port: 8000
```

> 💡 **Try changing these!** Edit `interval_seconds` to 5 and your time-lapse will take photos faster. Edit `web_port` to 9000 if port 8000 is busy.

📖 See [Configuration Guide](01%20-%20WebApp%20TimeLapse/docs/07_configuration_guide.md) for all options.

---

## 🖥️ CLI Commands

```bash
python main.py                    # Start web server
python main.py --debug            # Debug mode (auto-reloads when you change code)
python main.py validate           # Check configuration, packages, camera & permissions
python main.py sessions           # List all sessions
python main.py cleanup --days 7   # Delete sessions older than 7 days
python main.py init               # Create a default config file
```

📖 See [CLI & API Reference](01%20-%20WebApp%20TimeLapse/docs/09_cli_api_reference.md) for full details.

---

## 🧪 Try the Simple Scripts First

Before diving into the full web app, try these minimal scripts to understand the basics:

```bash
# The simplest time-lapse script (headless, ~80 lines)
python "01 - WebApp TimeLapse/simple.py"

# Time-lapse with live preview window (~200 lines)
python "01 - WebApp TimeLapse/simple_with_preview.py"
```

> 💡 Or `cd "01 - WebApp TimeLapse"` first and then just `python simple.py`.

These scripts have **extensive comments** explaining every step. Perfect for learning!

📖 See [Simple Script Guide](01%20-%20WebApp%20TimeLapse/docs/10_simple_script_guide.md) for a detailed walkthrough.

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

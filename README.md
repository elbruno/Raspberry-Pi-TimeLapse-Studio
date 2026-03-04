# 🎬 PiTimeLapse Lab

A beginner-friendly time-lapse studio that works on **Windows**, **macOS**, **Linux**, and **Raspberry Pi**! 📸

Capture photos using USB webcams, built-in laptop cameras, or Raspberry Pi cameras. Save them with timestamps and control everything through a **web browser** or a **touchscreen GUI**.

**Perfect for:**

- 🌅 Capturing sunsets and sunrises
- 🌱 Watching plants grow
- ☁️ Recording cloud movements
- 🏗️ Documenting projects
- 📚 Learning Python and Raspberry Pi!

---

## 📦 What's Inside

This repository contains **two complete time-lapse applications** and a set of **hands-on labs** for learning touchscreen development:

| Folder | What it is | Best for |
|--------|-----------|----------|
| [**01-WebApp-TimeLapse**](01-WebApp-TimeLapse/) | 🌐 Web-based time-lapse app with Flask | Any platform — control from your phone or computer |
| [**02-Touch-TimeLapse**](02-Touch-TimeLapse/) | 👆 Touchscreen GUI time-lapse app with Pygame | Raspberry Pi with a 3.5" touchscreen display |
| [**labs**](labs/) | 🧪 Hands-on LCD & touchscreen demos | Learning Raspberry Pi display programming |

---

## 🎯 Which Scenario Should I Use?

| | 01 — WebApp TimeLapse | 02 — Touch TimeLapse |
|---|---|---|
| **Interface** | Web browser (Flask) | Native touchscreen GUI (Pygame) |
| **Platform** | ✅ Windows, macOS, Linux, Raspberry Pi | 🍓 Raspberry Pi with touchscreen (dev mode on desktop) |
| **Control** | Remote — from any device on the network | On-device — tap the screen directly |
| **Camera** | USB webcam, built-in camera, Pi Camera | USB webcam, Pi Camera |
| **Best for** | Remote monitoring, multi-device access | Standalone field capture, kiosk setups |
| **Complexity** | Beginner-friendly with extensive docs | Intermediate — hardware setup required |

> 💡 **Not sure?** Start with **Scenario 01** — it works on any computer and doesn't require special hardware.

---

## �� Screenshots

### Scenario 01 — WebApp TimeLapse

| Dashboard | Gallery | Settings |
|-----------|---------|----------|
| ![Dashboard](01-WebApp-TimeLapse/images/01_dashboard.jpeg) | ![Gallery](01-WebApp-TimeLapse/images/02_gallery.jpeg) | ![Settings](01-WebApp-TimeLapse/images/03_settings.jpeg) |

---

## 🚀 Quick Start

### Scenario 01 — WebApp TimeLapse (Recommended)

```bash
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/01-WebApp-TimeLapse
pip install -r requirements.txt
python main.py validate         # Check your setup
python main.py                  # Open http://localhost:8000
```

> 💡 **Virtual environment optional.** On a dedicated Raspberry Pi you can install packages globally. On a shared/dev machine, use `python3 -m venv venv && source venv/bin/activate` first (Windows: `venv\Scripts\activate`).
>
> ⚠️ **PEP 668 error?** On newer Raspberry Pi OS, pip may refuse to install globally. Add `--break-system-packages` to the pip command — this is safe on a dedicated Pi.

📖 Full instructions → [**01-WebApp-TimeLapse/README.md**](01-WebApp-TimeLapse/README.md)

### Scenario 02 — Touch TimeLapse (Raspberry Pi)

```bash
git clone https://github.com/elbruno/Raspberry-Pi-TimeLapse-Studio.git
cd Raspberry-Pi-TimeLapse-Studio/02-Touch-TimeLapse
pip install -r requirements.txt
python timelapse_touch.py                  # Windowed (desktop dev)
python timelapse_touch.py --fullscreen     # Fullscreen (Pi LCD)
```

> 💡 **Virtual environment optional.** On a dedicated Pi this isn't needed. On a shared machine, create one first (see note above).
>
> ⚠️ **PEP 668 error?** Add `--break-system-packages` to the pip command (safe on a dedicated Pi).

📖 Full instructions → [**02-Touch-TimeLapse/README.md**](02-Touch-TimeLapse/README.md)

---

## 🎓 New to Programming? Start Here

This project is designed for **beginners**! If you're new to programming or Raspberry Pi:

1. **Start simple**: Try `simple.py` in Scenario 01 — it's just ~80 lines of code!
2. **Learn the concepts**: Check out [Python Basics](01-WebApp-TimeLapse/docs/02_python_basics_used.md)
3. **Don't worry about mistakes**: They're the best way to learn!

<details>
<summary><strong>📖 Beginner's Glossary - Click to expand!</strong></summary>

| Term | What it means |
|------|--------------|
| **Repository (repo)** | A folder containing all the project files, tracked by Git |
| **Clone** | Download a copy of a repository to your computer |
| **Terminal/Command Line** | A text interface to type commands (like PowerShell or Bash) |
| **Virtual Environment (venv)** | An optional private space for this project's Python packages — recommended on shared machines, not needed on a dedicated Raspberry Pi |
| **pip** | Python's package installer - downloads and installs Python libraries |
| **requirements.txt** | A list of Python packages this project needs |
| **Port** | A number that identifies where a program "listens" for connections (like 8000) |
| **localhost** | Your own computer - used to access web apps running on your machine |
| **Camera index** | A number identifying which camera to use (0 = first camera, 1 = second, etc.) |
| **OpenCV** | A popular library for working with cameras and images |
| **Flask** | A simple framework for building web applications in Python |
| **Pygame** | A library for making graphical applications and games in Python |
| **Framebuffer** | A low-level way to draw directly to a screen without a desktop environment |

</details>

---

## 📖 Documentation

### Scenario 01 — WebApp TimeLapse

| I want to... | Go to... |
|--------------|----------|
| 🎯 **Start learning (beginner)** | [Simple Script Guide](01-WebApp-TimeLapse/docs/10_simple_script_guide.md) ⬅️ Start here! |
| 🔧 **Set up from scratch** | [Installation Guide](01-WebApp-TimeLapse/docs/06_installation_guide.md) |
| ⚙️ **Configure settings** | [Configuration Guide](01-WebApp-TimeLapse/docs/07_configuration_guide.md) |
| 🐛 **Fix a problem** | [Troubleshooting](01-WebApp-TimeLapse/docs/08_troubleshooting.md) |
| 📡 **Use the API** | [CLI & API Reference](01-WebApp-TimeLapse/docs/09_cli_api_reference.md) |
| 📚 **Understand the code** | [Project Overview](01-WebApp-TimeLapse/docs/01_project_overview.md) |

### Scenario 02 — Touch TimeLapse

| I want to... | Go to... |
|--------------|----------|
| 👆 **Get started with the touchscreen app** | [Touch TimeLapse README](02-Touch-TimeLapse/README.md) |
| 🧪 **Try the LCD labs** | [Labs README](labs/README.md) |

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
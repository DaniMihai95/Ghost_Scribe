# 👻 Ghost Scribe

**Local AI Writing Assistant powered by Intel NPU**

> "Why send your clipboard to the cloud? Use the NPU you already paid for."

![Ghost Scribe](ghost_scribe.png)

## What is Ghost Scribe?

Ghost Scribe is a **100% offline** AI writing assistant that runs on your Intel Core Ultra laptop's Neural Processing Unit (NPU). It sits quietly in your system tray and springs into action when you press `Ctrl+Space`.

### Features

- 🚀 **NPU-Accelerated**: Runs on Intel Meteor Lake/Lunar Lake NPU
- 🔒 **100% Private**: Your data never leaves your laptop
- ⚡ **Instant Access**: Press `Ctrl+Space` anytime
- 🪶 **Lightweight**: ~50MB RAM when idle
- 🔋 **Battery Friendly**: NPU is optimized for efficiency

### What Can It Do?

| You Copy This | Ghost Scribe Does This |
|---------------|------------------------|
| Long article | Summarizes in bullet points |
| Code snippet | Reviews, comments, fixes bugs |
| Draft email | Rewrites professionally |
| Any text | Makes it clear and concise |

---

## Quick Start (Users)

### Download

Get the latest release from [Releases](../../releases) or [Gumroad](https://your-gumroad-link).

### Installation

1. **Extract** the `GhostScribe.zip` to any folder
2. **Run** `GhostScribe.exe`
3. **Wait** 5 seconds for NPU to warm up
4. **Look** for the green ghost icon in your system tray

### Usage

1. **Copy** any text (`Ctrl+C`)
2. **Press** `Ctrl+Space`
3. **Read** the AI-enhanced result
4. **Click** "Copy Result" to use it

---

## Developers

### Requirements

- Python 3.10+
- Intel Core Ultra processor (Meteor Lake or newer)
- Windows 11

### Setup

```bash
# Clone the repository
git clone https://github.com/DaniMihai95/Ghost_Scribe.git
cd Ghost_Scribe

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install openvino-genai keyboard pyperclip pystray pillow pyinstaller

# Run the app
python main.py
```

### Building from Source

```bash
# Run the build script
build.bat

# Or manually:
pyinstaller --noconfirm --onedir --windowed --name "GhostScribe" --icon=ghost_scribe.ico main.py

# Copy model folder to dist/GhostScribe/
xcopy /E /Y tinyllama-model dist\GhostScribe\tinyllama-model\
```

### Project Structure

```
ghost-scribe/
├── main.py              # Main application
├── create_icon.py       # Icon generator
├── build.bat            # Build script
├── ghost_scribe.ico     # Application icon
├── tinyllama-model/     # AI model files
│   ├── openvino_model.xml
│   ├── openvino_model.bin
│   ├── openvino_tokenizer.xml
│   └── ...
└── dist/
    └── GhostScribe/     # Distribution folder
        ├── GhostScribe.exe
        └── tinyllama-model/
```

---

## Troubleshooting

### "NPU not found" error

Make sure you have:
1. Intel Core Ultra processor (not regular Core i5/i7/i9)
2. Latest Intel NPU drivers from [Intel Driver Support](https://www.intel.com/content/www/us/en/support/detect.html)

### App crashes on startup

Try installing Visual C++ Redistributable 2022:
- [Download from Microsoft](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### Hotkey doesn't work

Some apps (like games) block global hotkeys. Try clicking on the desktop first, then press `Ctrl+Space`.

---

## License

MIT License - Feel free to use, modify, and distribute.

---

## Support the Project

If Ghost Scribe saves you time, consider:

- ⭐ Star this repo
- 💰 [Buy the packaged version](https://your-gumroad-link) ($9)
- 🐛 Report bugs and request features
- 🔧 Contribute code

---

Made with 💚 for Intel NPU | © 2026

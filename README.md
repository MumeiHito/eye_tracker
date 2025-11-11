# Eye Tracker Desktop Application

[English](README.md) | [日本語](README.ja.md)

![Python](https://img.shields.io/badge/python-3.12-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

Cross-platform desktop application (Windows and macOS) that monitors head pose and gaze using a single webcam. The tool detects when the user looks away from the screen and displays an always-on-top notification overlay.

## Screenshots

*Application with live camera feed and real-time face tracking*

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Calibration Workflow](#calibration-workflow)
- [Controls & Settings](#controls--settings)
- [Packaging with PyInstaller](#packaging-with-pyinstaller)
- [Contributing](#contributing)
- [License](#license)

## Features

- Real-time webcam capture (OpenCV) with MediaPipe face mesh and iris detection
- Head pose estimation via `solvePnP` with configurable smoothing
- Gaze vector calculation with guided calibration for centre and screen edges
- Persistent calibration data and application settings (`src/config.json`)
- PySide6 GUI with live video preview, overlays, and calibration controls
- Transparent overlay window that warns when attention drops
- Optional CSV logging for debugging or analysis
- PyInstaller packaging configuration for standalone executables

## Requirements

- Python 3.12
- Webcam accessible by the operating system
- Windows 10+ or macOS 12+ (tested manually)

Python dependencies are listed in `requirements.txt` (MediaPipe, OpenCV, PySide6, NumPy, SciPy, PyInstaller).

## Quick Start

1. **Clone and enter the project**

   ```bash
   git clone <repo-url> eye_tracker
   cd eye_tracker
   ```

2. **Create and activate the virtual environment (Python 3.12)**

   - macOS / Linux:

     ```bash
     python3.12 -m venv venv
     source venv/bin/activate
     ```

   - Windows (PowerShell):

     ```powershell
     python3.12 -m venv venv
     venv\Scripts\Activate.ps1
     ```

3. **Install dependencies**

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python -m src.main
   ```

   The first launch attempts to load `src/config.json`. If calibration data is missing or invalid, use the calibration buttons in the UI.

## Calibration Workflow

1. **Head pose calibration**
   - Sit comfortably facing the screen.
   - Click **Calibrate Head Pose**.
   - Keep still until the progress bar reaches 100%. The baseline angles are saved automatically.

2. **Gaze calibration**
   - Click **Calibrate Gaze**.
   - Follow the on-screen instructions (centre, left, right, up, down).
   - Each step collects several samples. After completion, gaze thresholds update automatically.

Calibration data and settings persist in `src/config.json`. Re-run calibration at any time if lighting conditions change or equipment moves.

## Controls & Settings

- **Camera index**: select the webcam device (0 is default).
- **Smoothing window**: moving-average window size for head pose and gaze values.
- **Warning delay**: number of consecutive frames out of range before the overlay appears.
- **Overlay toggle**: enable/disable the always-on-top alert window.
- **Head pose thresholds**: allowable deviation (degrees) from the calibrated baseline for yaw, pitch, and roll.
- **Gaze thresholds**: acceptable horizontal/vertical ranges (normalised) around the calibrated values.
- **Logging**: enable in `src/config.json` (`"log_to_csv": true`) to write `logs/tracking_log.csv`.

## Overlay Window

The overlay is a borderless, transparent window that displays a warning message when both head pose and gaze exceed thresholds for longer than the configured delay. The overlay hides automatically when the user returns attention to the screen.

## Packaging with PyInstaller

### Automated Build (Recommended)

1. Activate the project virtual environment:
   
   **Windows:**
   ```powershell
   venv\Scripts\Activate.ps1
   ```
   
   **macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

2. Run the build script:
   
   **Windows:**
   ```bash
   build_exe.bat
   ```
   
   **macOS/Linux:**
   ```bash
   chmod +x build_exe.sh
   ./build_exe.sh
   ```

3. The executable will be in `dist/EyeTracker.exe` (one file) or `dist/EyeTracker/` directory (one folder).

   **Current mode:** One-File (single executable)
   - 📦 `dist/EyeTracker.exe` - standalone executable (~400-500 MB)
   - ⚠️ First startup may take 5-10 seconds (unpacking to temp folder)
   - ✅ Easy to distribute - just one file!

   To switch to One-Folder mode (faster startup), see [ONE_FILE_BUILD.md](ONE_FILE_BUILD.md).

### Manual Build

If you prefer to build manually:

1. Activate the virtual environment.
2. Ensure dependencies are installed (`pip install -r requirements.txt`).
3. Run PyInstaller using the provided spec file:

   ```bash
   pyinstaller EyeTracker.spec
   ```

4. The bundled application appears in the `dist/EyeTracker/` directory.

### Important Notes

- **MediaPipe Files:** The spec file automatically includes MediaPipe model files (.binarypb). If you encounter `FileNotFoundError` for MediaPipe modules, ensure the spec file is used.
- **Config File:** The application creates `config.json` on first run if it doesn't exist.
- **Cross-Platform:** The same spec file works on Windows, macOS, and Linux.
- **Icon:** To add a custom icon, add `icon='assets/app.ico'` to the `EXE()` section in `EyeTracker.spec`.

### Troubleshooting Build Issues

- **Import Errors:** Ensure you're running PyInstaller from within the activated virtual environment.
- **Missing MediaPipe Files:** The spec file should handle this automatically. If issues persist, verify MediaPipe is installed in the venv.
- **Large File Size:** The bundled app includes all dependencies and is typically 200-400 MB. This is normal for MediaPipe applications.

## Project Structure

```
.
├── assets/                  # optional icons or images
├── requirements.txt
├── env_setup.sh
├── README.md
└── src/
    ├── main.py              # PySide6 GUI
    ├── gaze_head_tracker.py # MediaPipe processing and logic
    ├── calibration.py       # Calibration data management
    ├── overlay.py           # Always-on-top warning window
    ├── utils.py             # Helpers for smoothing and math
    └── config.json          # Persistent settings & calibration data
```

## Troubleshooting

- **No camera feed**: verify the correct camera index and that no other app is using the webcam.
- **Laggy video**: reduce the smoothing window or ensure adequate system resources.
- **False alerts**: recalibrate in the current lighting and adjust thresholds using the settings panel.
- **Packaging errors**: ensure PyInstaller is run inside the virtual environment and include MediaPipe resource files by default (PyInstaller copies them automatically when installed via pip).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Clone the repository
2. Create a Python 3.12 virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Run the application: `python -m src.main`

For detailed build instructions, see [PACKAGING_GUIDE.md](PACKAGING_GUIDE.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

This project uses the following third-party libraries:
- **MediaPipe** - Apache License 2.0
- **PySide6** - LGPLv3
- **OpenCV** - Apache License 2.0
- **NumPy** - BSD License
- **SciPy** - BSD License

For full license texts, refer to the respective projects' documentation.

## Acknowledgments

- Google MediaPipe team for the face detection models
- Qt Company for PySide6
- OpenCV community for computer vision tools

## Support

- Report bugs via [GitHub Issues](https://github.com/YOUR_USERNAME/eye_tracker/issues)
- See [CONTRIBUTING.md](CONTRIBUTING.md) for development questions
- Check existing [documentation](README.md) first

## Star History

If you find this project useful, please consider giving it a star ⭐


# Contributing to Eye Tracker

Thank you for your interest in contributing to the Eye Tracker project!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/eye_tracker.git
   cd eye_tracker
   ```

2. Create a virtual environment with Python 3.12:
   ```bash
   python3.12 -m venv venv
   ```

3. Activate the virtual environment:
   - **Windows:** `venv\Scripts\Activate.ps1`
   - **macOS/Linux:** `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. Run the application:
   ```bash
   python -m src.main
   ```

## Project Structure

```
eye_tracker/
├── src/                    # Source code
│   ├── main.py            # Application entry point
│   ├── calibration.py     # Calibration data management
│   ├── gaze_head_tracker.py  # Core tracking logic
│   ├── overlay.py         # Warning overlay window
│   ├── utils.py           # Helper functions
│   ├── config.json        # User config (gitignored)
│   └── config.json.example # Config template
├── assets/                 # Optional icons/images
├── build_exe.bat          # Windows build script
├── build_exe.sh           # macOS/Linux build script
├── EyeTracker.spec        # PyInstaller spec file
├── hook-mediapipe.py      # PyInstaller hook for MediaPipe
├── check_mediapipe_files.py  # Build verification script
├── requirements.txt       # Python dependencies
├── README.md              # English documentation
├── README.ja.md           # Japanese documentation
├── PACKAGING_GUIDE.md     # PyInstaller build guide
└── env_setup.sh           # Environment setup script
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Keep comments in English only
- Maximum line length: 120 characters

## Making Changes

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and test thoroughly:
   ```bash
   python -m src.main
   ```

3. Test the build process:
   ```bash
   pyinstaller EyeTracker.spec
   ```

4. Commit your changes:
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

6. Create a Pull Request on GitHub

## Testing

Before submitting a pull request:

- [ ] Application runs without errors from source
- [ ] PyInstaller build completes successfully
- [ ] Built executable runs without errors
- [ ] Camera detection works
- [ ] Face mesh detection works
- [ ] Calibration saves and loads correctly
- [ ] Overlay appears correctly
- [ ] Settings persist after restart

## Reporting Issues

When reporting issues, please include:

1. Operating system and version
2. Python version
3. Steps to reproduce
4. Expected behavior
5. Actual behavior
6. Error messages (if any)
7. Screenshots (if applicable)

## Feature Requests

Feature requests are welcome! Please:

1. Check existing issues first
2. Describe the feature clearly
3. Explain why it would be useful
4. Provide examples if possible

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Questions?

If you have questions, feel free to:
- Open an issue with the "question" label
- Check existing documentation
- Review closed issues for similar questions

Thank you for contributing!


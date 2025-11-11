@echo off
echo Building EyeTracker executable...
echo.

REM Check if virtual environment is activated
if not defined VIRTUAL_ENV (
    echo Error: Virtual environment not activated!
    echo Please run: venv\Scripts\activate
    exit /b 1
)

echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist EyeTracker.spec.backup del EyeTracker.spec.backup

echo.
echo Checking MediaPipe installation...
python -c "import mediapipe; print('MediaPipe version:', mediapipe.__version__)" || (
    echo Error: MediaPipe not found in virtual environment!
    echo Please run: pip install -r requirements.txt
    exit /b 1
)

echo.
echo Running PyInstaller with custom spec file...
pyinstaller EyeTracker.spec

echo.
if exist dist\EyeTracker\EyeTracker.exe (
    echo Build successful!
    echo Executable location: dist\EyeTracker\EyeTracker.exe
    echo.
    echo You can now run the application from dist\EyeTracker\EyeTracker.exe
) else (
    echo Build failed! Check the output above for errors.
    exit /b 1
)

pause


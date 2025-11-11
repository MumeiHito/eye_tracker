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
if exist dist\EyeTracker.exe (
    echo Build successful!
    echo.
    echo ===================================================
    echo   ONE-FILE BUILD COMPLETE
    echo ===================================================
    echo   Executable location: dist\EyeTracker.exe
    echo   File size: 
    for %%A in (dist\EyeTracker.exe) do echo   %%~zA bytes
    echo.
    echo   You can now run: dist\EyeTracker.exe
    echo.
    echo   Note: First startup may take 5-10 seconds
    echo         (unpacking to temp folder)
    echo ===================================================
) else (
    echo Build failed! Check the output above for errors.
    exit /b 1
)

pause


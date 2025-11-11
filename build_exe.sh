#!/bin/bash

echo "Building EyeTracker executable..."
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Virtual environment not activated!"
    echo "Please run: source venv/bin/activate"
    exit 1
fi

echo "Cleaning previous build..."
rm -rf build dist

echo ""
echo "Running PyInstaller..."
pyinstaller EyeTracker.spec

echo ""
if [ -f "dist/EyeTracker/EyeTracker" ]; then
    echo "Build successful!"
    echo "Executable location: dist/EyeTracker/EyeTracker"
    echo ""
    echo "You can now run the application from dist/EyeTracker/EyeTracker"
else
    echo "Build failed! Check the output above for errors."
    exit 1
fi


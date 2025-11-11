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
if [ -f "dist/EyeTracker" ]; then
    echo "Build successful!"
    echo ""
    echo "==================================================="
    echo "  ONE-FILE BUILD COMPLETE"
    echo "==================================================="
    echo "  Executable location: dist/EyeTracker"
    echo "  File size: $(du -h dist/EyeTracker | cut -f1)"
    echo ""
    echo "  You can now run: ./dist/EyeTracker"
    echo ""
    echo "  Note: First startup may take 5-10 seconds"
    echo "        (unpacking to temp folder)"
    echo "==================================================="
else
    echo "Build failed! Check the output above for errors."
    exit 1
fi


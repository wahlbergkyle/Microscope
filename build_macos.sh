#!/bin/bash
# macOS build script for Webcam App
# Run this on macOS to create Webcam_App.app

set -e

echo "Starting macOS build for Webcam App..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.7 or higher."
    echo "Recommended: Install via Homebrew: brew install python"
    exit 1
fi

echo "Python found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Install macOS specific dependencies if needed
echo "Installing macOS specific dependencies..."
pip install py2app 2>/dev/null || echo "py2app not needed for PyInstaller"

# Create icons if they don't exist
if [ ! -f "webcam_app.png" ]; then
    echo "Creating application icons..."
    python create_icon.py
fi

# Clean previous build
if [ -d "build" ]; then
    rm -rf build
fi
if [ -d "dist" ]; then
    rm -rf dist
fi

# Build the application
echo "Building macOS app bundle..."
pyinstaller --clean Webcam_App_macOS.spec

if [ $? -eq 0 ]; then
    echo
    echo "SUCCESS: macOS app bundle created!"
    echo "Location: dist/Webcam_App.app"
    
    # Show app size
    APP_SIZE=$(du -sh "dist/Webcam_App.app" | cut -f1)
    echo "App size: $APP_SIZE"
    
    # Try to create DMG if create-dmg is available
    if command -v create-dmg &> /dev/null; then
        echo "Creating DMG installer..."
        create-dmg \
            --volname "Webcam App Installer" \
            --window-pos 200 120 \
            --window-size 800 400 \
            --icon-size 100 \
            --icon "Webcam_App.app" 200 190 \
            --hide-extension "Webcam_App.app" \
            --app-drop-link 600 185 \
            "dist/Webcam_App_Installer.dmg" \
            "dist/" 2>/dev/null || echo "DMG creation skipped (optional)"
    else
        echo "Note: Install create-dmg for DMG installer: brew install create-dmg"
    fi
    
    echo
    echo "To install:"
    echo "1. Drag dist/Webcam_App.app to /Applications/ folder"
    echo "2. Or double-click the app to run from current location"
    echo "3. Grant camera permissions when prompted"
    echo
    echo "The app is now ready to use on macOS!"
    
else
    echo "ERROR: Build failed!"
    exit 1
fi
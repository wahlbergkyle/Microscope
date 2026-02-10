#!/bin/bash
# Webcam Application Launcher
# This script ensures the executable runs with proper environment

# Get the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXECUTABLE="$SCRIPT_DIR/dist/Webcam_App"

# Check if the executable exists
if [ ! -f "$EXECUTABLE" ]; then
    zenity --error --text="Webcam App executable not found at:\n$EXECUTABLE" 2>/dev/null || \
    echo "Error: Webcam App executable not found at: $EXECUTABLE"
    exit 1
fi

# Check if the executable is... executable
if [ ! -x "$EXECUTABLE" ]; then
    chmod +x "$EXECUTABLE"
fi

# Set up environment
export QT_QPA_PLATFORM_PLUGIN_PATH=""
export QT_QPA_PLATFORM=""

# Try to run the application
if ! "$EXECUTABLE" 2>&1; then
    # If it fails, show an error dialog if possible
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --width=400 --text="Failed to launch Webcam App.\n\nPossible issues:\n• No camera connected\n• Camera in use by another application\n• Missing system libraries\n\nTry running from terminal for detailed error messages:\n$EXECUTABLE"
    else
        echo "Failed to launch Webcam App. Try running from terminal: $EXECUTABLE"
    fi
    exit 1
fi
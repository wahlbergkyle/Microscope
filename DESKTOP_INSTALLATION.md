# Desktop Installation Guide - Webcam App

This guide explains how to build and install the Webcam App as a desktop executable on Windows, macOS, and Linux.

## Overview

The Webcam App can be compiled into standalone executables for all major desktop platforms:

- **Windows**: `Webcam_App.exe` - Single executable file
- **macOS**: `Webcam_App.app` - Application bundle 
- **Linux**: `Webcam_App` - Executable binary

All executables are self-contained and include the Python runtime, so no Python installation is required on the target machine.

### What's Been Created:

1. **Standalone Executable**: `dist/Webcam_App` (~96MB)
   - Contains all Python dependencies
   - No need for Python installation on target machines
   - Includes OpenCV, NumPy, PIL, and Tkinter

2. **Desktop Shortcut**: `~/Desktop/Webcam_App.desktop`
   - Double-click to launch the application
   - Includes custom webcam icon
   - Integrated with system application menu

3. **Launch Script**: `launch_webcam_app.sh`
   - Provides better error handling
   - Shows user-friendly error messages
   - Handles runtime environment setup

### How to Use:

#### Quick Start:
- **Double-click** the "Webcam App" icon on your desktop
- The GUI will open with all webcam controls available

#### Features Available:
- ✅ Real-time webcam preview
- ✅ Photo capture with custom filenames
- ✅ Video recording with duration control
- ✅ Manual exposure and gain control
- ✅ Timelapse photography with consistent settings
- ✅ Multiple camera support

### Distribution:

The `dist/Webcam_App` executable is **completely self-contained** and can be:
- Copied to any Linux x86_64 system
- Shared with others (no Python installation required)
- Moved to different locations (update desktop shortcut path accordingly)

### Troubleshooting:

#### Application Won't Start:
- Ensure your camera is connected and not in use by another app
- Right-click the desktop icon → Properties → Permissions → Allow executing
- Run from terminal for detailed error messages: `./dist/Webcam_App`

#### No Camera Detected:
- Check USB connection
- Try different USB port
- Close other camera applications (Zoom, Skype, etc.)
- On some systems, add your user to the video group:
  ```bash
  sudo usermod -a -G video $USER
  ```
  (Then log out and back in)

#### Permission Issues:
- Make sure both files are executable:
  ```bash
  chmod +x ~/Desktop/Webcam_App.desktop
  chmod +x "/home/kyle/U of M/Microscope/launch_webcam_app.sh"
  ```

### File Locations:

- **Desktop Shortcut**: `~/Desktop/Webcam_App.desktop`
- **Main Executable**: `/home/kyle/U of M/Microscope/dist/Webcam_App`
- **Launch Script**: `/home/kyle/U of M/Microscope/launch_webcam_app.sh`
- **Icon**: `/home/kyle/U of M/Microscope/webcam_app.png`
- **Source Code**: `/home/kyle/U of M/Microscope/src/`

### Technical Details:

- **Size**: ~96MB (includes Python runtime and all dependencies)
- **Platform**: Linux x86_64
- **Dependencies**: Self-contained (no external requirements)
- **Python Version**: 3.12.11 (embedded)
- **OpenCV Version**: 4.8.0+

---

**Enjoy your new webcam application!** 📸

For questions or issues, check the source code in the `src/` directory or run the application from terminal to see detailed error messages.
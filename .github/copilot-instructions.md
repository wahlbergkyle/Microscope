# USB Webcam Application - Copilot Instructions

This project is a complete Python application for controlling USB-connected webcams using OpenCV.

## Features
- Real-time webcam feed display with GUI interface
- Photo capture and video recording capabilities
- Command-line interface for automation
- Multiple camera support and detection
- Cross-platform compatibility (Windows, macOS, Linux)

## Project Structure
- `src/webcam_app.py` - Main GUI application
- `src/webcam_cli.py` - Command-line interface
- `src/camera_controller.py` - Core camera operations
- `src/utils.py` - Utility functions
- `examples/` - Usage examples and demos
- `tests/` - Unit tests with pytest
- `requirements.txt` - Python dependencies

## Usage
**GUI Application:** Run `python src/webcam_app.py`
**CLI Application:** Run `python src/webcam_cli.py --help`
**Examples:** Run scripts in `examples/` directory

## Development Guidelines
- Use OpenCV for all camera operations
- Implement proper resource cleanup with context managers
- Handle camera connection errors gracefully
- Follow PEP 8 style guidelines
- Test with multiple camera configurations
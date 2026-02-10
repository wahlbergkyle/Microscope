# USB Webcam Application

A Python application for controlling USB-connected webcams using OpenCV. This application provides real-time webcam feed display, photo capture, video recording, and an intuitive GUI interface.

## Features

- **Real-time webcam feed**: Live video display from USB cameras
- **Photo capture**: Take and save photos in various formats (JPG, PNG, BMP)
- **Video recording**: Record video with customizable settings
- **Timelapse photography**: Capture photo series with consistent settings and intervals
- **Exposure & Gain Control**: Manual control of camera exposure time and gain settings
- **Auto/Manual Exposure**: Switch between automatic and manual exposure modes
- **GUI interface**: User-friendly interface built with Tkinter
- **Multi-camera support**: Detect and switch between multiple USB cameras
- **Cross-platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.7 or higher
- USB webcam connected to your computer
- Required Python packages (see requirements.txt)

## Installation

1. Clone or download this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### GUI Application
Run the main GUI application:
```bash
python src/webcam_app.py
```

### Command Line Interface
For basic webcam operations:
```bash
python src/webcam_cli.py
```

### Examples
Check the `examples/` directory for various usage examples:
- `basic_capture.py` - Simple photo capture
- `video_recording.py` - Video recording example
- `multiple_cameras.py` - Working with multiple cameras
- `exposure_gain_control.py` - Camera exposure and gain control examples
- `timelapse_series.py` - Timelapse photography with consistent settings

### Camera Control Options

#### GUI Application
The GUI includes intuitive controls for:
- **Auto Exposure Toggle**: Enable/disable automatic exposure
- **Exposure Slider**: Manual exposure control (typically -13.0 to -1.0)
- **Gain Slider**: Camera gain adjustment (typically 0.0 to 100.0)
- **Timelapse Controls**: Set photo count and interval for automated series capture
- Real-time feedback showing current camera settings and capture progress

#### Command Line Interface
```bash
# Take photo with manual exposure and gain
python src/webcam_cli.py --photo --exposure -8.0 --gain 50

# Record video with auto exposure
python src/webcam_cli.py --video --duration 10 --auto-exposure

# Capture timelapse series (10 photos, 5-second intervals)
python src/webcam_cli.py --timelapse --count 10 --interval 5 --exposure -7.0 --gain 30

# Show camera info including exposure ranges
python src/webcam_cli.py --info
```

### Timelapse Photography

#### GUI Timelapse
1. Set desired photo count and interval using the spinboxes
2. Optionally adjust exposure and gain settings for consistency
3. Click "Start Timelapse" to begin automated capture
4. Monitor progress in the status area
5. Click "Stop Timelapse" to interrupt if needed

#### CLI Timelapse
```bash
# Basic timelapse: 20 photos every 30 seconds
python src/webcam_cli.py --timelapse --count 20 --interval 30

# Timelapse with manual settings for consistency
python src/webcam_cli.py --timelapse --count 50 --interval 10 \
  --exposure -6.0 --gain 25 --output-dir sunset_timelapse

# Custom filename base
python src/webcam_cli.py --timelapse --count 100 --interval 5 \
  --base-name "plant_growth" --output-dir timelapse_project
```

## Project Structure

```
├── src/
│   ├── webcam_app.py          # Main GUI application
│   ├── webcam_cli.py          # Command line interface
│   ├── camera_controller.py   # Camera operations class
│   └── utils.py               # Utility functions
├── examples/
│   ├── basic_capture.py       # Basic photo capture
│   ├── video_recording.py     # Video recording example
│   ├── multiple_cameras.py    # Multiple camera handling
│   ├── exposure_gain_control.py # Manual camera control examples
│   └── timelapse_series.py    # Timelapse photography examples
├── tests/
│   ├── test_camera.py         # Camera controller tests
│   └── test_utils.py          # Utility function tests
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## Troubleshooting

### Camera Not Detected
- Ensure your USB camera is properly connected
- Check that no other applications are using the camera
- Try different USB ports
- On Linux, you may need to add your user to the `video` group:
  ```bash
  sudo usermod -a -G video $USER
  ```

### Permission Errors
- On macOS, grant camera permissions in System Preferences > Security & Privacy
- On Windows, check camera privacy settings

### Installation Issues
- Ensure you have the latest pip version:
  ```bash
  pip install --upgrade pip
  ```
- If OpenCV installation fails, try:
  ```bash
  pip install opencv-python-headless
  ```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
This project follows PEP 8 style guidelines. Use `black` for formatting:
```bash
pip install black
black src/ examples/ tests/
```

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
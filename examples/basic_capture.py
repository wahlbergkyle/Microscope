#!/usr/bin/env python3
"""
Basic Camera Capture Example

This example demonstrates basic webcam operations:
- Initialize camera
- Capture a single photo
- Display camera information
- Proper resource cleanup
"""

import sys
import os

# Add src directory to path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from camera_controller import CameraController
from utils import ensure_directory_exists


def main():
    """Main function demonstrating basic camera capture."""
    print("Basic Camera Capture Example")
    print("=" * 40)
    
    # Create output directory
    output_dir = "example_photos"
    ensure_directory_exists(output_dir)
    
    # Initialize camera using context manager for automatic cleanup
    with CameraController(camera_index=0) as camera:
        if not camera.initialize_camera():
            print("Error: Could not initialize camera")
            print("Please check:")
            print("- Camera is connected")
            print("- No other applications are using the camera")
            print("- Camera drivers are installed")
            return False
        
        # Display camera information
        print("\nCamera Information:")
        properties = camera.get_camera_properties()
        if properties:
            print(f"  Resolution: {properties['width']} x {properties['height']}")
            print(f"  FPS: {properties['fps']}")
            print(f"  Brightness: {properties.get('brightness', 'N/A')}")
            print(f"  Contrast: {properties.get('contrast', 'N/A')}")
        else:
            print("  Could not retrieve camera properties")
        
        # List available cameras
        print("\nAvailable Cameras:")
        available_cameras = camera.list_available_cameras()
        if available_cameras:
            for cam_idx in available_cameras:
                print(f"  Camera {cam_idx}")
        else:
            print("  No cameras detected")
        
        # Capture a photo
        print(f"\nCapturing photo...")
        filename = "example_basic_capture.jpg"
        
        if camera.take_photo(filename, output_dir):
            print(f"✓ Photo saved successfully: {output_dir}/{filename}")
            
            # Display file information
            filepath = os.path.join(output_dir, filename)
            file_size = os.path.getsize(filepath)
            print(f"  File size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
        else:
            print("✗ Failed to capture photo")
            return False
        
        # Demonstrate multiple quick captures
        print(f"\nCapturing 3 quick photos...")
        for i in range(3):
            filename = f"example_quick_{i+1}.jpg"
            if camera.take_photo(filename, output_dir):
                print(f"  ✓ Photo {i+1} saved: {filename}")
            else:
                print(f"  ✗ Failed to capture photo {i+1}")
        
        print(f"\nAll photos saved to: {os.path.abspath(output_dir)}")
        
    print("\nExample completed successfully!")
    return True


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
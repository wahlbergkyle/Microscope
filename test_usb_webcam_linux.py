#!/usr/bin/env python3
"""
USB Webcam Diagnostics Tool for Linux

This script helps diagnose and fix common USB webcam issues on Linux,
particularly the "black screen" problem that's common with USB cameras.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import cv2
import time
from camera_controller import CameraController

def test_opencv_backends():
    """Test different OpenCV backends."""
    print("=== OpenCV Backend Test ===\n")
    
    backends = [
        (cv2.CAP_V4L2, "V4L2"),
        (cv2.CAP_V4L, "V4L"),
        (cv2.CAP_ANY, "AUTO"),
    ]
    
    # Try to add GStreamer if available
    try:
        backends.append((cv2.CAP_GSTREAMER, "GStreamer"))
    except:
        pass
    
    camera_index = 0
    
    for backend_id, backend_name in backends:
        print(f"Testing {backend_name} backend...")
        try:
            cap = cv2.VideoCapture(camera_index, backend_id)
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    frame_mean = frame.mean()
                    print(f"  ✓ {backend_name}: Working (frame mean: {frame_mean:.2f})")
                    if frame_mean <= 1.0:
                        print(f"    WARNING: Frame appears black!")
                else:
                    print(f"  ✗ {backend_name}: Cannot read frames")
                cap.release()
            else:
                print(f"  ✗ {backend_name}: Cannot open camera")
        except Exception as e:
            print(f"  ✗ {backend_name}: Error - {e}")
        print()

def test_camera_properties():
    """Test different camera property settings."""
    print("=== Camera Properties Test ===\n")
    
    controller = CameraController(0)
    if not controller.initialize_camera():
        print("Cannot initialize camera for property testing")
        return
    
    # Test different resolutions
    resolutions = [
        (640, 480),
        (800, 600),
        (1280, 720),
        (1920, 1080)
    ]
    
    print("Testing resolutions:")
    for width, height in resolutions:
        controller.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        controller.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        actual_width = int(controller.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(controller.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        ret, frame = controller.cap.read()
        if ret and frame is not None:
            frame_mean = frame.mean()
            print(f"  {width}x{height} -> {actual_width}x{actual_height}: "
                  f"{'✓' if frame_mean > 1.0 else '✗'} (mean: {frame_mean:.2f})")
        else:
            print(f"  {width}x{height}: ✗ Cannot read frame")
    
    print("\nTesting pixel formats:")
    formats = [
        ('MJPG', cv2.VideoWriter_fourcc('M','J','P','G')),
        ('YUYV', cv2.VideoWriter_fourcc('Y','U','Y','V')),
    ]
    
    for format_name, fourcc in formats:
        controller.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        ret, frame = controller.cap.read()
        if ret and frame is not None:
            frame_mean = frame.mean()
            print(f"  {format_name}: {'✓' if frame_mean > 1.0 else '✗'} (mean: {frame_mean:.2f})")
        else:
            print(f"  {format_name}: ✗ Cannot read frame")
    
    controller.release()

def test_usb_reset():
    """Test USB camera reset techniques."""
    print("=== USB Reset Test ===\n")
    
    print("Testing multiple camera open/close cycles...")
    
    for cycle in range(3):
        print(f"Cycle {cycle + 1}:")
        
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            # Flush several frames
            for _ in range(10):
                cap.read()
            
            ret, frame = cap.read()
            if ret and frame is not None:
                frame_mean = frame.mean()
                print(f"  Frame mean: {frame_mean:.2f} {'✓' if frame_mean > 1.0 else '✗'}")
            else:
                print("  ✗ Cannot read frame")
        else:
            print("  ✗ Cannot open camera")
        
        cap.release()
        time.sleep(1)  # Wait between cycles

def main():
    """Run all diagnostic tests."""
    print("USB Webcam Linux Diagnostics")
    print("=" * 40)
    print()
    
    # Check if any cameras are available
    print("Scanning for cameras...")
    controller = CameraController()
    cameras = controller.list_available_cameras()
    
    if not cameras:
        print("❌ No cameras found!")
        return
    
    print(f"✓ Found cameras: {cameras}")
    print()
    
    # Run diagnostic tests
    test_opencv_backends()
    test_camera_properties()
    test_usb_reset()
    
    print("\n=== Recommendations ===")
    print("If you're experiencing black screens:")
    print("1. Try the 'Fix Camera' button in the GUI")
    print("2. Unplug and reconnect the USB camera")
    print("3. Try a different USB port")
    print("4. Check if camera works with: cheese, guvcview, or vlc")
    print("5. Ensure no other applications are using the camera")
    print("6. Try running: sudo modprobe uvcvideo")

if __name__ == "__main__":
    main()
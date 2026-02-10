#!/usr/bin/env python3
"""
Test script for camera auto-detection functionality.

This script tests the improved camera detection system to ensure
USB webcams can be found regardless of their video device number.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from camera_controller import CameraController

def test_camera_detection():
    """Test the camera auto-detection system."""
    print("=== Camera Detection Test ===\n")
    
    # Test 1: List available cameras
    print("1. Scanning for available cameras...")
    controller = CameraController()
    cameras = controller.list_available_cameras()
    
    if cameras:
        print(f"✓ Found {len(cameras)} working camera(s): {cameras}")
    else:
        print("✗ No cameras found")
        return False
    
    # Test 2: Auto-detection with different starting indices
    print("\n2. Testing auto-detection with different starting indices...")
    
    for test_index in [0, 1, 2, 5, 10]:  # Test various starting points
        print(f"\n   Testing with camera_index={test_index}...")
        test_controller = CameraController(test_index)
        
        if test_controller.initialize_camera():
            actual_index = test_controller.camera_index
            print(f"   ✓ Auto-detected camera at index {actual_index}")
            
            # Get camera info
            info = test_controller.get_camera_info()
            if info['available']:
                print(f"     Resolution: {info['width']}x{info['height']}")
                print(f"     FPS: {info['fps']:.1f}")
            
            test_controller.release()
        else:
            print(f"   ✗ Failed to initialize camera")
    
    # Test 3: Camera info for all detected cameras
    print("\n3. Detailed information for all cameras...")
    for cam_idx in cameras:
        info = controller.get_camera_info(cam_idx)
        print(f"\n   Camera {cam_idx}:")
        print(f"     Available: {info['available']}")
        if info['available']:
            print(f"     Resolution: {info['width']}x{info['height']}")
            print(f"     FPS: {info['fps']:.1f}")
            print(f"     Backend: {info['backend']}")
    
    print("\n=== Test Complete ===")
    return True

if __name__ == "__main__":
    test_camera_detection()
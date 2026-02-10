#!/usr/bin/env python3
"""
Exposure and Gain Control Example

This example demonstrates how to control camera exposure time and gain:
- Setting manual exposure values
- Adjusting camera gain
- Switching between auto and manual exposure
- Capturing photos with different settings
"""

import sys
import os
import time

# Add src directory to path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from camera_controller import CameraController
from utils import ensure_directory_exists


def main():
    """Main function demonstrating exposure and gain control."""
    print("Exposure and Gain Control Example")
    print("=" * 40)
    
    # Create output directory
    output_dir = "example_exposure_gain"
    ensure_directory_exists(output_dir)
    
    # Initialize camera
    with CameraController(camera_index=0) as camera:
        if not camera.initialize_camera():
            print("Error: Could not initialize camera")
            return False
        
        # Display initial camera settings
        print("\nInitial Camera Settings:")
        properties = camera.get_camera_properties()
        if properties:
            print(f"  Current Exposure: {properties.get('exposure', 'N/A')}")
            print(f"  Current Gain: {properties.get('gain', 'N/A')}")
            print(f"  Auto Exposure: {properties.get('auto_exposure', 'N/A')}")
        
        # Get supported ranges
        exp_range = camera.get_exposure_range()
        gain_range = camera.get_gain_range()
        print(f"\nSupported Ranges:")
        print(f"  Exposure: {exp_range[0]:.1f} to {exp_range[1]:.1f}")
        print(f"  Gain: {gain_range[0]:.1f} to {gain_range[1]:.1f}")
        
        # Example 1: Auto exposure photo
        print(f"\n1. Taking photo with auto exposure...")
        camera.set_auto_exposure(True)
        time.sleep(1)  # Allow camera to adjust
        
        if camera.take_photo("auto_exposure.jpg", output_dir):
            print("   ✓ Auto exposure photo saved")
        else:
            print("   ✗ Failed to capture auto exposure photo")
        
        # Example 2: Manual exposure - dark (underexposed)
        print(f"\n2. Taking photo with manual exposure (dark)...")
        camera.set_auto_exposure(False)
        camera.set_exposure_time(-12.0)  # Very short exposure (dark)
        camera.set_gain(0.0)  # Low gain
        time.sleep(0.5)  # Brief pause for setting to take effect
        
        if camera.take_photo("manual_dark.jpg", output_dir):
            print("   ✓ Dark exposure photo saved")
        else:
            print("   ✗ Failed to capture dark photo")
        
        # Example 3: Manual exposure - bright (overexposed)
        print(f"\n3. Taking photo with manual exposure (bright)...")
        camera.set_exposure_time(-3.0)  # Longer exposure (brighter)
        camera.set_gain(50.0)  # Higher gain
        time.sleep(0.5)
        
        if camera.take_photo("manual_bright.jpg", output_dir):
            print("   ✓ Bright exposure photo saved")
        else:
            print("   ✗ Failed to capture bright photo")
        
        # Example 4: Balanced manual settings
        print(f"\n4. Taking photo with balanced manual settings...")
        camera.set_exposure_time(-6.0)  # Medium exposure
        camera.set_gain(25.0)  # Medium gain
        time.sleep(0.5)
        
        if camera.take_photo("manual_balanced.jpg", output_dir):
            print("   ✓ Balanced exposure photo saved")
        else:
            print("   ✗ Failed to capture balanced photo")
        
        # Example 5: High gain, low exposure
        print(f"\n5. Taking photo with high gain, low exposure...")
        camera.set_exposure_time(-10.0)  # Short exposure
        camera.set_gain(80.0)  # High gain (may introduce noise)
        time.sleep(0.5)
        
        if camera.take_photo("high_gain_low_exp.jpg", output_dir):
            print("   ✓ High gain photo saved")
        else:
            print("   ✗ Failed to capture high gain photo")
        
        # Example 6: Series of photos with different exposures
        print(f"\n6. Taking exposure series...")
        exposure_values = [-12.0, -9.0, -6.0, -3.0]
        
        for i, exposure in enumerate(exposure_values, 1):
            print(f"   Taking photo {i}/4 with exposure {exposure}...")
            camera.set_exposure_time(exposure)
            camera.set_gain(10.0)  # Keep gain constant
            time.sleep(0.5)
            
            filename = f"exposure_series_{abs(exposure):.0f}.jpg"
            if camera.take_photo(filename, output_dir):
                print(f"     ✓ Series photo {i} saved")
            else:
                print(f"     ✗ Failed to capture series photo {i}")
        
        # Display final settings
        print(f"\nFinal Camera Settings:")
        final_properties = camera.get_camera_properties()
        if final_properties:
            print(f"  Final Exposure: {final_properties.get('exposure', 'N/A')}")
            print(f"  Final Gain: {final_properties.get('gain', 'N/A')}")
        
        # Reset to auto exposure
        print(f"\nResetting to auto exposure...")
        camera.set_auto_exposure(True)
        
        print(f"\n✓ All photos saved to: {os.path.abspath(output_dir)}")
        
        # Display tips
        print(f"\nTips for Exposure and Gain Control:")
        print(f"- Lower exposure values = darker images (shorter exposure time)")
        print(f"- Higher exposure values = brighter images (longer exposure time)")
        print(f"- Higher gain = brighter but potentially noisier images")
        print(f"- Use auto exposure for general purposes")
        print(f"- Use manual exposure for consistent lighting conditions")
        print(f"- Experiment with different combinations for your use case")
    
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
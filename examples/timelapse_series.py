#!/usr/bin/env python3
"""
Timelapse Series Example

This example demonstrates how to capture timelapse photo series:
- Basic timelapse with regular intervals
- Timelapse with consistent camera settings
- Different interval patterns
- Progress monitoring and interruption handling
"""

import sys
import os
import time

# Add src directory to path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from camera_controller import CameraController
from utils import ensure_directory_exists


class TimelapseExample:
    """Example class demonstrating timelapse functionality."""
    
    def __init__(self):
        """Initialize the example."""
        self.camera = None
    
    def basic_timelapse(self, output_dir="example_timelapse_basic"):
        """
        Demonstrate basic timelapse functionality.
        
        Args:
            output_dir (str): Output directory for photos
        """
        print("Basic Timelapse Example")
        print("-" * 30)
        
        ensure_directory_exists(output_dir)
        
        with CameraController(camera_index=0) as camera:
            if not camera.initialize_camera():
                print("Error: Could not initialize camera")
                return False
            
            # Basic timelapse: 5 photos, 2 second intervals
            print("Capturing 5 photos with 2-second intervals...")
            
            def progress_callback(current, total, filename):
                """Simple progress display."""
                print(f"  📸 Photo {current}/{total}: {filename}")
            
            captured_files = camera.capture_timelapse_series(
                num_photos=5,
                interval_seconds=2.0,
                output_dir=output_dir,
                base_filename="basic_timelapse",
                progress_callback=progress_callback
            )
            
            if captured_files:
                print(f"✓ Basic timelapse complete!")
                print(f"  Files: {len(captured_files)} photos in {output_dir}")
                return True
            else:
                print("✗ Basic timelapse failed")
                return False
    
    def consistent_settings_timelapse(self, output_dir="example_timelapse_consistent"):
        """
        Demonstrate timelapse with consistent camera settings.
        
        Args:
            output_dir (str): Output directory for photos
        """
        print("\nConsistent Settings Timelapse Example")
        print("-" * 40)
        
        ensure_directory_exists(output_dir)
        
        with CameraController(camera_index=0) as camera:
            if not camera.initialize_camera():
                print("Error: Could not initialize camera")
                return False
            
            print("Capturing 8 photos with fixed exposure and gain settings...")
            print("Settings: Manual exposure -7.0, Gain 20.0, 3-second intervals")
            
            def detailed_progress_callback(current, total, filename):
                """Detailed progress with timing."""
                remaining = total - current
                est_time = remaining * 3.0  # 3 second intervals
                print(f"  📸 Photo {current}/{total}: {filename}")
                if remaining > 0:
                    print(f"      ⏱ Next photo in 3 seconds, ~{est_time:.0f}s remaining")
            
            captured_files = camera.capture_timelapse_series(
                num_photos=8,
                interval_seconds=3.0,
                output_dir=output_dir,
                base_filename="consistent_settings",
                exposure=-7.0,  # Fixed exposure
                gain=20.0,      # Fixed gain
                auto_exposure=False,  # Manual mode for consistency
                progress_callback=detailed_progress_callback
            )
            
            if captured_files:
                print(f"✓ Consistent settings timelapse complete!")
                print(f"  Files: {len(captured_files)} photos in {output_dir}")
                print("  All photos captured with identical camera settings")
                return True
            else:
                print("✗ Consistent settings timelapse failed")
                return False
    
    def rapid_timelapse(self, output_dir="example_timelapse_rapid"):
        """
        Demonstrate rapid timelapse with short intervals.
        
        Args:
            output_dir (str): Output directory for photos
        """
        print("\nRapid Timelapse Example")
        print("-" * 25)
        
        ensure_directory_exists(output_dir)
        
        with CameraController(camera_index=0) as camera:
            if not camera.initialize_camera():
                print("Error: Could not initialize camera")
                return False
            
            print("Capturing 15 photos with 0.5-second intervals (rapid fire)...")
            
            def rapid_progress_callback(current, total, filename):
                """Compact progress for rapid capture."""
                print(f"📸 {current}/{total}", end=" ", flush=True)
                if current % 5 == 0 or current == total:
                    print()  # New line every 5 photos or at end
            
            start_time = time.time()
            
            captured_files = camera.capture_timelapse_series(
                num_photos=15,
                interval_seconds=0.5,
                output_dir=output_dir,
                base_filename="rapid_timelapse",
                auto_exposure=True,  # Auto exposure for rapid changes
                progress_callback=rapid_progress_callback
            )
            
            end_time = time.time()
            total_time = end_time - start_time
            
            if captured_files:
                print(f"\n✓ Rapid timelapse complete!")
                print(f"  Files: {len(captured_files)} photos in {output_dir}")
                print(f"  Total time: {total_time:.1f} seconds")
                print(f"  Average rate: {len(captured_files)/total_time:.1f} photos/second")
                return True
            else:
                print("\n✗ Rapid timelapse failed")
                return False
    
    def interrupted_timelapse_demo(self, output_dir="example_timelapse_interrupt"):
        """
        Demonstrate timelapse with interruption capability.
        
        Args:
            output_dir (str): Output directory for photos
        """
        print("\nInterrupted Timelapse Demo")
        print("-" * 27)
        print("This will start a longer timelapse that you can interrupt with Ctrl+C")
        
        ensure_directory_exists(output_dir)
        
        with CameraController(camera_index=0) as camera:
            if not camera.initialize_camera():
                print("Error: Could not initialize camera")
                return False
            
            print("Starting 20-photo timelapse with 4-second intervals...")
            print("Press Ctrl+C at any time to stop early")
            
            def interrupt_progress_callback(current, total, filename):
                """Progress display with interrupt instructions."""
                remaining = total - current
                est_time = remaining * 4.0
                print(f"  📸 Photo {current}/{total}: {filename}")
                print(f"      ⏱ {remaining} photos remaining, ~{est_time:.0f}s (Ctrl+C to stop)")
            
            try:
                captured_files = camera.capture_timelapse_series(
                    num_photos=20,
                    interval_seconds=4.0,
                    output_dir=output_dir,
                    base_filename="interrupt_demo",
                    exposure=-6.0,
                    gain=15.0,
                    auto_exposure=False,
                    progress_callback=interrupt_progress_callback
                )
                
                print(f"\n✓ Full timelapse completed!")
                print(f"  Files: {len(captured_files)} photos in {output_dir}")
                return True
                
            except KeyboardInterrupt:
                print(f"\n⚠ Timelapse interrupted by user!")
                # Check what files were actually captured
                import glob
                pattern = os.path.join(output_dir, "interrupt_demo_*.jpg")
                existing_files = glob.glob(pattern)
                print(f"  Partial capture: {len(existing_files)} photos saved")
                return True  # Partial success
    
    def variable_interval_example(self, output_dir="example_timelapse_variable"):
        """
        Demonstrate timelapse with variable intervals using multiple series.
        
        Args:
            output_dir (str): Output directory for photos
        """
        print("\nVariable Interval Example")
        print("-" * 27)
        print("Capturing multiple short series with different intervals")
        
        ensure_directory_exists(output_dir)
        
        with CameraController(camera_index=0) as camera:
            if not camera.initialize_camera():
                print("Error: Could not initialize camera")
                return False
            
            intervals = [1.0, 2.0, 3.0]  # Different intervals
            all_files = []
            
            for i, interval in enumerate(intervals, 1):
                print(f"\nSeries {i}: 3 photos with {interval}s intervals")
                
                def series_progress_callback(current, total, filename):
                    print(f"  Series {i} - Photo {current}/{total}: {filename}")
                
                captured_files = camera.capture_timelapse_series(
                    num_photos=3,
                    interval_seconds=interval,
                    output_dir=output_dir,
                    base_filename=f"variable_series{i}",
                    exposure=-8.0,  # Consistent exposure across all series
                    gain=25.0,      # Consistent gain across all series
                    auto_exposure=False,
                    progress_callback=series_progress_callback
                )
                
                all_files.extend(captured_files)
                
                if i < len(intervals):
                    print(f"  Pausing 2 seconds before next series...")
                    time.sleep(2)
            
            print(f"\n✓ Variable interval example complete!")
            print(f"  Total files: {len(all_files)} photos in {output_dir}")
            print(f"  Series captured with intervals: {', '.join(f'{i}s' for i in intervals)}")
            return True


def main():
    """Main function demonstrating timelapse examples."""
    print("Timelapse Series Examples")
    print("=" * 40)
    
    example = TimelapseExample()
    
    try:
        # Example 1: Basic timelapse
        if not example.basic_timelapse():
            print("Skipping remaining examples due to camera error")
            return False
        
        # Wait between examples
        time.sleep(2)
        
        # Example 2: Consistent settings
        if not example.consistent_settings_timelapse():
            print("Example 2 failed")
        
        time.sleep(2)
        
        # Example 3: Rapid timelapse
        if not example.rapid_timelapse():
            print("Example 3 failed")
        
        time.sleep(2)
        
        # Example 4: Variable intervals
        if not example.variable_interval_example():
            print("Example 4 failed")
        
        # Example 5: Interrupted timelapse (commented out for automatic testing)
        print(f"\nTo test interruption capability, run:")
        print(f"python {__file__} --interrupt")
        
        print(f"\n🎉 All timelapse examples completed!")
        print(f"\nTips for Timelapse Photography:")
        print(f"- Use consistent camera settings for uniform appearance")
        print(f"- Consider the total duration vs interval for your subject")
        print(f"- Shorter intervals for fast-changing subjects")
        print(f"- Longer intervals for slow changes (clouds, shadows, etc.)")
        print(f"- Use manual exposure to avoid flickering between shots")
        print(f"- Ensure stable camera mounting for best results")
        
        return True
    
    except Exception as e:
        print(f"Error during examples: {e}")
        return False


if __name__ == "__main__":
    try:
        # Check for interrupt demo flag
        if len(sys.argv) > 1 and sys.argv[1] == "--interrupt":
            example = TimelapseExample()
            example.interrupted_timelapse_demo()
        else:
            success = main()
            if not success:
                sys.exit(1)
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
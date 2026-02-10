#!/usr/bin/env python3
"""
Multiple Cameras Example

This example demonstrates working with multiple USB cameras:
- Detect available cameras
- Switch between cameras
- Capture from multiple cameras simultaneously
- Compare camera properties
"""

import sys
import os
import time
import threading

# Add src directory to path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from camera_controller import CameraController
from utils import ensure_directory_exists


class MultipleCamerasExample:
    """Example class for multiple camera operations."""
    
    def __init__(self):
        """Initialize the example."""
        self.cameras = {}
        self.active_recordings = {}
    
    def scan_and_list_cameras(self):
        """
        Scan for and list all available cameras with their properties.
        
        Returns:
            list: List of available camera indices
        """
        print("Scanning for Available Cameras")
        print("-" * 50)
        
        # Use temporary controller to scan
        temp_controller = CameraController()
        available_cameras = temp_controller.list_available_cameras()
        
        if not available_cameras:
            print("No cameras found!")
            return []
        
        print(f"Found {len(available_cameras)} camera(s):\n")
        
        for camera_index in available_cameras:
            print(f"Camera {camera_index}:")
            
            # Initialize camera to get properties
            camera = CameraController(camera_index)
            if camera.initialize_camera():
                properties = camera.get_camera_properties()
                if properties:
                    print(f"  Resolution: {properties['width']} x {properties['height']}")
                    print(f"  FPS: {properties['fps']}")
                    print(f"  Brightness: {properties.get('brightness', 'N/A')}")
                    print(f"  Contrast: {properties.get('contrast', 'N/A')}")
                else:
                    print("  Could not retrieve properties")
                
                camera.release()
            else:
                print("  Failed to initialize")
            
            print()  # Empty line for spacing
        
        return available_cameras
    
    def capture_from_all_cameras(self, available_cameras, output_dir="example_multi_photos"):
        """
        Capture photos from all available cameras.
        
        Args:
            available_cameras (list): List of camera indices
            output_dir (str): Output directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not available_cameras:
            print("No cameras available for capture")
            return False
        
        print("Capturing Photos from All Cameras")
        print("-" * 50)
        
        ensure_directory_exists(output_dir)
        
        success_count = 0
        
        for camera_index in available_cameras:
            print(f"Capturing from Camera {camera_index}...", end=" ")
            
            with CameraController(camera_index) as camera:
                if camera.initialize_camera():
                    filename = f"camera_{camera_index}_capture.jpg"
                    
                    if camera.take_photo(filename, output_dir):
                        print("✓ Success")
                        success_count += 1
                    else:
                        print("✗ Failed to capture")
                else:
                    print("✗ Failed to initialize")
        
        print(f"\nCapture Summary: {success_count}/{len(available_cameras)} cameras successful")
        
        if success_count > 0:
            print(f"Photos saved to: {os.path.abspath(output_dir)}")
        
        return success_count > 0
    
    def simultaneous_recording(self, available_cameras, duration=10, 
                             output_dir="example_multi_videos"):
        """
        Record from multiple cameras simultaneously.
        
        Args:
            available_cameras (list): List of camera indices
            duration (int): Recording duration in seconds
            output_dir (str): Output directory
            
        Returns:
            bool: True if at least one recording succeeded
        """
        if not available_cameras:
            print("No cameras available for recording")
            return False
        
        print(f"Simultaneous Recording from {len(available_cameras)} Cameras")
        print(f"Duration: {duration} seconds")
        print("-" * 50)
        
        ensure_directory_exists(output_dir)
        
        # Initialize all cameras
        initialized_cameras = {}
        
        for camera_index in available_cameras:
            camera = CameraController(camera_index)
            if camera.initialize_camera():
                filename = f"camera_{camera_index}_simultaneous.mp4"
                if camera.start_recording(filename, output_dir):
                    initialized_cameras[camera_index] = camera
                    print(f"✓ Camera {camera_index} recording started")
                else:
                    print(f"✗ Camera {camera_index} failed to start recording")
                    camera.release()
            else:
                print(f"✗ Camera {camera_index} failed to initialize")
        
        if not initialized_cameras:
            print("No cameras could start recording")
            return False
        
        # Start recording threads
        print(f"\nRecording from {len(initialized_cameras)} cameras...")
        
        recording_threads = {}
        self.active_recordings = {idx: True for idx in initialized_cameras.keys()}
        
        for camera_index, camera in initialized_cameras.items():
            thread = threading.Thread(
                target=self._recording_worker, 
                args=(camera_index, camera, duration)
            )
            thread.start()
            recording_threads[camera_index] = thread
        
        # Monitor progress
        start_time = time.time()
        while time.time() - start_time < duration:
            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed
            active_count = sum(self.active_recordings.values())
            
            print(f"\rProgress: {elapsed}/{duration}s, Active cameras: {active_count}", 
                  end="", flush=True)
            time.sleep(1)
        
        print("\nStopping recordings...")
        
        # Stop all recordings
        for camera_index in initialized_cameras.keys():
            self.active_recordings[camera_index] = False
        
        # Wait for threads to complete
        for thread in recording_threads.values():
            thread.join()
        
        # Stop recording and cleanup
        successful_recordings = 0
        
        for camera_index, camera in initialized_cameras.items():
            if camera.stop_recording():
                print(f"✓ Camera {camera_index} recording saved")
                successful_recordings += 1
            else:
                print(f"✗ Camera {camera_index} recording failed")
            
            camera.release()
        
        print(f"\nRecording Summary: {successful_recordings}/{len(initialized_cameras)} successful")
        
        if successful_recordings > 0:
            print(f"Videos saved to: {os.path.abspath(output_dir)}")
        
        return successful_recordings > 0
    
    def _recording_worker(self, camera_index, camera, duration):
        """
        Worker function for recording from a single camera.
        
        Args:
            camera_index (int): Camera index
            camera: Camera controller instance
            duration (int): Recording duration
        """
        start_time = time.time()
        
        while (self.active_recordings.get(camera_index, False) and 
               time.time() - start_time < duration):
            camera.record_frame()
            time.sleep(0.033)  # ~30 FPS
    
    def compare_camera_properties(self, available_cameras):
        """
        Compare properties of all available cameras.
        
        Args:
            available_cameras (list): List of camera indices
        """
        if not available_cameras:
            print("No cameras available for comparison")
            return
        
        print("Camera Properties Comparison")
        print("-" * 50)
        
        # Collect properties from all cameras
        camera_properties = {}
        
        for camera_index in available_cameras:
            with CameraController(camera_index) as camera:
                if camera.initialize_camera():
                    properties = camera.get_camera_properties()
                    if properties:
                        camera_properties[camera_index] = properties
                    else:
                        camera_properties[camera_index] = {"error": "Could not retrieve properties"}
                else:
                    camera_properties[camera_index] = {"error": "Failed to initialize"}
        
        if not camera_properties:
            print("No camera properties could be retrieved")
            return
        
        # Display comparison table
        print(f"{'Camera':<8} {'Resolution':<12} {'FPS':<5} {'Brightness':<10} {'Contrast':<10}")
        print("-" * 55)
        
        for camera_index, props in camera_properties.items():
            if "error" in props:
                print(f"{camera_index:<8} {props['error']}")
            else:
                resolution = f"{props.get('width', 'N/A')}x{props.get('height', 'N/A')}"
                fps = str(props.get('fps', 'N/A'))
                brightness = f"{props.get('brightness', 'N/A'):.2f}" if props.get('brightness') is not None else "N/A"
                contrast = f"{props.get('contrast', 'N/A'):.2f}" if props.get('contrast') is not None else "N/A"
                
                print(f"{camera_index:<8} {resolution:<12} {fps:<5} {brightness:<10} {contrast:<10}")
        
        # Find best camera based on resolution
        best_camera = None
        best_resolution = 0
        
        for camera_index, props in camera_properties.items():
            if "error" not in props and "width" in props and "height" in props:
                resolution_pixels = props["width"] * props["height"]
                if resolution_pixels > best_resolution:
                    best_resolution = resolution_pixels
                    best_camera = camera_index
        
        if best_camera is not None:
            print(f"\nRecommended camera (highest resolution): Camera {best_camera}")
        
        print()


def main():
    """Main function demonstrating multiple camera examples."""
    print("Multiple Cameras Examples")
    print("=" * 40)
    
    example = MultipleCamerasExample()
    
    try:
        # Step 1: Scan for available cameras
        available_cameras = example.scan_and_list_cameras()
        
        if not available_cameras:
            print("No cameras found. Please connect USB cameras and try again.")
            return False
        
        if len(available_cameras) == 1:
            print("Only one camera found. Some examples will be limited.")
        
        # Step 2: Compare camera properties
        example.compare_camera_properties(available_cameras)
        
        # Step 3: Capture from all cameras
        print("\n" + "="*50)
        if not example.capture_from_all_cameras(available_cameras):
            print("Photo capture example failed")
        
        # Step 4: Simultaneous recording (only if multiple cameras)
        if len(available_cameras) > 1:
            time.sleep(2)  # Brief pause
            print("\n" + "="*50)
            if not example.simultaneous_recording(available_cameras, duration=8):
                print("Simultaneous recording example failed")
        else:
            print("\nSkipping simultaneous recording (only one camera available)")
        
        print("\n✓ Multiple cameras examples completed!")
        return True
    
    except Exception as e:
        print(f"Error during examples: {e}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nExamples interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
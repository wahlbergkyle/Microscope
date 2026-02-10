#!/usr/bin/env python3
"""
USB Webcam Application - Command Line Interface

A command-line interface for basic webcam operations including
photo capture, video recording, and camera information display.

Usage:
    python webcam_cli.py [options]

Examples:
    python webcam_cli.py --photo
    python webcam_cli.py --video --duration 10
    python webcam_cli.py --info
    python webcam_cli.py --list-cameras
"""

import argparse
import os
import sys
import time
import signal
from datetime import datetime

from camera_controller import CameraController
from utils import ensure_directory_exists, get_timestamp_filename


class WebcamCLI:
    """Command-line interface for webcam operations."""
    
    def __init__(self):
        """Initialize the CLI application."""
        self.camera_controller = None
        self.recording = False
        
        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals for graceful shutdown."""
        print("\nShutting down gracefully...")
        self.recording = False
        if self.camera_controller:
            if self.camera_controller.is_recording:
                self.camera_controller.stop_recording()
            self.camera_controller.release()
        sys.exit(0)
    
    def initialize_camera(self, camera_index=0):
        """
        Initialize camera connection.
        
        Args:
            camera_index (int): Index of camera to use
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.camera_controller = CameraController(camera_index)
        
        if self.camera_controller.initialize_camera():
            print(f"Camera {camera_index} initialized successfully")
            return True
        else:
            print(f"Failed to initialize camera {camera_index}")
            return False
    
    def apply_camera_settings(self, exposure=None, gain=None, auto_exposure=None):
        """
        Apply camera settings for exposure and gain.
        
        Args:
            exposure (float, optional): Exposure value to set
            gain (float, optional): Gain value to set
            auto_exposure (bool, optional): Enable/disable auto exposure
        """
        if not self.camera_controller:
            return
        
        if auto_exposure is not None:
            success = self.camera_controller.set_auto_exposure(auto_exposure)
            if success:
                mode = "enabled" if auto_exposure else "disabled"
                print(f"Auto exposure {mode}")
            else:
                print("Failed to set auto exposure mode")
        
        if exposure is not None and not auto_exposure:
            success = self.camera_controller.set_exposure_time(exposure)
            if success:
                print(f"Exposure set to {exposure}")
            else:
                print(f"Failed to set exposure to {exposure}")
        
        if gain is not None:
            success = self.camera_controller.set_gain(gain)
            if success:
                print(f"Gain set to {gain}")
            else:
                print(f"Failed to set gain to {gain}")
    
    def list_cameras(self):
        """List all available cameras with detailed information."""
        print("Scanning for available cameras...")
        
        # Create temporary controller to scan for cameras
        temp_controller = CameraController()
        available_cameras = temp_controller.list_available_cameras()
        
        if available_cameras:
            print(f"\nFound {len(available_cameras)} working camera(s):")
            for camera_index in available_cameras:
                info = temp_controller.get_camera_info(camera_index)
                print(f"\n  Camera {camera_index}:")
                if info['available']:
                    print(f"    Status: Available")
                    if info['width'] and info['height']:
                        print(f"    Resolution: {info['width']} x {info['height']}")
                    if info['fps']:
                        print(f"    FPS: {info['fps']:.1f}")
                    if info['backend']:
                        print(f"    Backend: {info['backend']}")
                else:
                    print(f"    Status: Not available")
        else:
            print("No cameras found")
        
        return available_cameras
    
    def show_camera_info(self, camera_index=0):
        """
        Display detailed camera information.
        
        Args:
            camera_index (int): Camera index to query
        """
        print(f"Camera {camera_index} Information:")
        print("-" * 30)
        
        if not self.initialize_camera(camera_index):
            return False
        
        properties = self.camera_controller.get_camera_properties()
        
        if properties:
            print(f"Resolution: {properties.get('width', 'N/A')} x {properties.get('height', 'N/A')}")
            print(f"FPS: {properties.get('fps', 'N/A')}")
            print(f"Brightness: {properties.get('brightness', 'N/A'):.2f}")
            print(f"Contrast: {properties.get('contrast', 'N/A'):.2f}")
            print(f"Saturation: {properties.get('saturation', 'N/A'):.2f}")
            print(f"Exposure: {properties.get('exposure', 'N/A'):.2f}")
            print(f"Gain: {properties.get('gain', 'N/A'):.2f}")
            
            auto_exp = properties.get('auto_exposure', 'N/A')
            if auto_exp == 0.75:
                auto_exp_text = "Auto"
            elif auto_exp == 0.25:
                auto_exp_text = "Manual"
            else:
                auto_exp_text = f"{auto_exp:.2f}"
            print(f"Auto Exposure: {auto_exp_text}")
            
            # Display supported ranges
            if self.camera_controller:
                exp_range = self.camera_controller.get_exposure_range()
                gain_range = self.camera_controller.get_gain_range()
                if exp_range != (0.0, 0.0):
                    print(f"Exposure Range: {exp_range[0]:.1f} to {exp_range[1]:.1f}")
                if gain_range != (0.0, 0.0):
                    print(f"Gain Range: {gain_range[0]:.1f} to {gain_range[1]:.1f}")
        else:
            print("Could not retrieve camera properties")
        
        self.camera_controller.release()
        return True
    
    def take_photo(self, camera_index=0, output_dir="photos", filename=None, 
                  exposure=None, gain=None, auto_exposure=None):
        """
        Capture a single photo.
        
        Args:
            camera_index (int): Camera index to use
            output_dir (str): Output directory
            filename (str, optional): Custom filename
            exposure (float, optional): Exposure setting
            gain (float, optional): Gain setting
            auto_exposure (bool, optional): Auto exposure setting
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Taking photo with camera {camera_index}...")
        
        if not self.initialize_camera(camera_index):
            return False
        
        # Apply camera settings
        self.apply_camera_settings(exposure, gain, auto_exposure)
        
        ensure_directory_exists(output_dir)
        
        if filename is None:
            filename = get_timestamp_filename("photo", "jpg")
        
        if self.camera_controller.take_photo(filename, output_dir):
            print(f"Photo saved: {output_dir}/{filename}")
            success = True
        else:
            print("Failed to take photo")
            success = False
        
        self.camera_controller.release()
        return success
    
    def record_video(self, camera_index=0, output_dir="videos", 
                    filename=None, duration=None, exposure=None, gain=None, auto_exposure=None):
        """
        Record video.
        
        Args:
            camera_index (int): Camera index to use
            output_dir (str): Output directory
            filename (str, optional): Custom filename
            duration (int, optional): Recording duration in seconds
            exposure (float, optional): Exposure setting
            gain (float, optional): Gain setting
            auto_exposure (bool, optional): Auto exposure setting
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Starting video recording with camera {camera_index}...")
        
        if not self.initialize_camera(camera_index):
            return False
        
        # Apply camera settings
        self.apply_camera_settings(exposure, gain, auto_exposure)
        
        ensure_directory_exists(output_dir)
        
        if filename is None:
            filename = get_timestamp_filename("video", "mp4")
        
        if not self.camera_controller.start_recording(filename, output_dir):
            print("Failed to start recording")
            self.camera_controller.release()
            return False
        
        self.recording = True
        start_time = time.time()
        
        print(f"Recording started. Press Ctrl+C to stop.")
        if duration:
            print(f"Recording will stop automatically after {duration} seconds.")
        
        try:
            while self.recording:
                if not self.camera_controller.record_frame():
                    print("Error recording frame")
                    break
                
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Print progress every 5 seconds
                if int(elapsed) % 5 == 0 and elapsed > 0:
                    print(f"Recording... {int(elapsed)} seconds")
                    time.sleep(1)  # Avoid printing multiple times per second
                
                # Check duration limit
                if duration and elapsed >= duration:
                    print(f"Recording complete ({duration} seconds)")
                    break
                
                time.sleep(0.033)  # ~30 FPS
        
        except KeyboardInterrupt:
            print("\nRecording interrupted by user")
        
        self.recording = False
        
        if self.camera_controller.stop_recording():
            print(f"Video saved: {output_dir}/{filename}")
            success = True
        else:
            print("Error stopping recording")
            success = False
        
        self.camera_controller.release()
        return success
    
    def capture_timelapse(self, camera_index=0, num_photos=10, interval_seconds=5.0,
                         output_dir="timelapse", base_filename=None,
                         exposure=None, gain=None, auto_exposure=None):
        """
        Capture timelapse series of photos.
        
        Args:
            camera_index (int): Camera index to use
            num_photos (int): Number of photos to capture
            interval_seconds (float): Time interval between photos
            output_dir (str): Output directory
            base_filename (str, optional): Base filename for photos
            exposure (float, optional): Exposure setting
            gain (float, optional): Gain setting
            auto_exposure (bool, optional): Auto exposure setting
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Starting timelapse capture with camera {camera_index}...")
        print(f"Photos: {num_photos}, Interval: {interval_seconds}s")
        
        if not self.initialize_camera(camera_index):
            return False
        
        # Apply camera settings
        self.apply_camera_settings(exposure, gain, auto_exposure)
        
        def progress_callback(current, total, filename):
            """Progress callback for timelapse capture."""
            percentage = (current / total) * 100
            print(f"  Progress: {current}/{total} ({percentage:.1f}%) - {filename}")
        
        try:
            captured_files = self.camera_controller.capture_timelapse_series(
                num_photos=num_photos,
                interval_seconds=interval_seconds,
                output_dir=output_dir,
                base_filename=base_filename,
                exposure=exposure,
                gain=gain,
                auto_exposure=auto_exposure,
                progress_callback=progress_callback
            )
            
            if captured_files:
                print(f"\n✓ Timelapse complete!")
                print(f"  Captured: {len(captured_files)} photos")
                print(f"  Location: {os.path.abspath(output_dir)}")
                print(f"  Files: {captured_files[0]} ... {captured_files[-1]}")
                success = True
            else:
                print("\n✗ No photos were captured")
                success = False
        
        except KeyboardInterrupt:
            print("\n⚠ Timelapse interrupted by user")
            success = False
        
        except Exception as e:
            print(f"\n✗ Error during timelapse: {e}")
            success = False
        
        self.camera_controller.release()
        return success

    def live_preview(self, camera_index=0):
        """
        Show live camera preview (text-based info).
        
        Args:
            camera_index (int): Camera index to use
        """
        print(f"Starting live preview with camera {camera_index}...")
        print("Press Ctrl+C to stop preview")
        
        if not self.initialize_camera(camera_index):
            return False
        
        frame_count = 0
        start_time = time.time()
        
        try:
            while True:
                frame = self.camera_controller.get_frame()
                if frame is not None:
                    frame_count += 1
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    if elapsed >= 1.0:  # Update every second
                        fps = frame_count / elapsed
                        height, width = frame.shape[:2]
                        print(f"Preview: {width}x{height} @ {fps:.1f} FPS")
                        frame_count = 0
                        start_time = current_time
                else:
                    print("No frame received")
                    time.sleep(0.1)
                
                time.sleep(0.033)  # ~30 FPS
        
        except KeyboardInterrupt:
            print("\nPreview stopped by user")
        
        self.camera_controller.release()
        return True


def main():
    """Main function for CLI application."""
    parser = argparse.ArgumentParser(
        description="USB Webcam Command Line Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --photo                              # Take a photo with default camera
  %(prog)s --photo --camera 1                   # Take a photo with camera 1
  %(prog)s --photo --exposure -8.0 --gain 50    # Take photo with custom exposure and gain
  %(prog)s --photo --auto-exposure              # Take photo with auto exposure
  %(prog)s --video --duration 30                # Record 30 seconds of video
  %(prog)s --video --output videos/             # Record video to specific directory
  %(prog)s --video --exposure -6.0 --gain 25    # Record with manual exposure settings
  %(prog)s --timelapse --count 20 --interval 2  # Take 20 photos every 2 seconds
  %(prog)s --timelapse --count 100 --interval 60 --exposure -7 --gain 30  # Hourly timelapse
  %(prog)s --timelapse --base-name "sunset"     # Custom filename base
  %(prog)s --info --camera 1                    # Show info for camera 1
  %(prog)s --list-cameras                       # List all available cameras
  %(prog)s --preview                            # Show live preview
        """
    )
    
    # Main actions (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument("--photo", action="store_true",
                            help="Take a single photo")
    action_group.add_argument("--video", action="store_true",
                            help="Record video")
    action_group.add_argument("--timelapse", action="store_true",
                            help="Capture timelapse series")
    action_group.add_argument("--info", action="store_true",
                            help="Show camera information")
    action_group.add_argument("--list-cameras", action="store_true",
                            help="List available cameras")
    action_group.add_argument("--preview", action="store_true",
                            help="Show live preview (text-based)")
    
    # Options
    parser.add_argument("--camera", type=int, default=0,
                       help="Camera index to use (default: 0)")
    parser.add_argument("--output", type=str,
                       help="Output directory (default: photos/ or videos/)")
    parser.add_argument("--filename", type=str,
                       help="Custom filename (default: auto-generated)")
    parser.add_argument("--duration", type=int,
                       help="Video recording duration in seconds")
    parser.add_argument("--exposure", type=float,
                       help="Set exposure time (typically -13.0 to -1.0)")
    parser.add_argument("--gain", type=float,
                       help="Set camera gain (typically 0.0 to 100.0)")
    parser.add_argument("--auto-exposure", action="store_true",
                       help="Enable auto exposure mode")
    
    # Timelapse options
    parser.add_argument("--count", type=int, default=10,
                       help="Number of photos for timelapse (default: 10)")
    parser.add_argument("--interval", type=float, default=5.0,
                       help="Time interval between photos in seconds (default: 5.0)")
    parser.add_argument("--base-name", type=str,
                       help="Base filename for timelapse photos (default: auto-generated)")
    
    args = parser.parse_args()
    
    # Create CLI instance
    cli = WebcamCLI()
    
    try:
        if args.list_cameras:
            cli.list_cameras()
        
        elif args.info:
            cli.show_camera_info(args.camera)
        
        elif args.photo:
            output_dir = args.output or "photos"
            cli.take_photo(args.camera, output_dir, args.filename, 
                          args.exposure, args.gain, args.auto_exposure)
        
        elif args.video:
            output_dir = args.output or "videos"
            cli.record_video(args.camera, output_dir, args.filename, args.duration,
                            args.exposure, args.gain, args.auto_exposure)
        
        elif args.timelapse:
            output_dir = args.output or "timelapse"
            cli.capture_timelapse(args.camera, args.count, args.interval, output_dir,
                                args.base_name, args.exposure, args.gain, args.auto_exposure)
        
        elif args.preview:
            cli.live_preview(args.camera)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
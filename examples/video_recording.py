#!/usr/bin/env python3
"""
Video Recording Example

This example demonstrates video recording capabilities:
- Start/stop recording
- Record for a specific duration
- Handle recording interruption
- Monitor recording progress
"""

import sys
import os
import time
import threading

# Add src directory to path to import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from camera_controller import CameraController
from utils import ensure_directory_exists


class VideoRecordingExample:
    """Example class for video recording operations."""
    
    def __init__(self):
        """Initialize the example."""
        self.camera = None
        self.recording_active = False
    
    def record_with_duration(self, duration_seconds=10, output_dir="example_videos"):
        """
        Record video for a specific duration.
        
        Args:
            duration_seconds (int): Recording duration in seconds
            output_dir (str): Output directory for video files
        """
        print(f"Recording Example: {duration_seconds} second video")
        print("-" * 50)
        
        ensure_directory_exists(output_dir)
        
        with CameraController(camera_index=0) as camera:
            if not camera.initialize_camera():
                print("Error: Could not initialize camera")
                return False
            
            # Display camera info
            properties = camera.get_camera_properties()
            if properties:
                print(f"Recording at: {properties['width']}x{properties['height']} @ {properties['fps']} FPS")
            
            # Start recording
            filename = f"example_duration_{duration_seconds}s.mp4"
            
            if not camera.start_recording(filename, output_dir):
                print("Failed to start recording")
                return False
            
            print(f"Recording started: {filename}")
            print("Progress: ", end="", flush=True)
            
            # Record for specified duration
            start_time = time.time()
            frame_count = 0
            
            try:
                while True:
                    current_time = time.time()
                    elapsed = current_time - start_time
                    
                    # Check if duration reached
                    if elapsed >= duration_seconds:
                        break
                    
                    # Record frame
                    if camera.record_frame():
                        frame_count += 1
                    
                    # Show progress every second
                    if int(elapsed) != int(elapsed - 0.033):
                        progress = int(elapsed)
                        remaining = duration_seconds - progress
                        print(f"\rProgress: {progress}/{duration_seconds}s (remaining: {remaining}s)", 
                              end="", flush=True)
                    
                    time.sleep(0.033)  # ~30 FPS
            
            except KeyboardInterrupt:
                print("\nRecording interrupted by user")
            
            # Stop recording
            if camera.stop_recording():
                print(f"\n✓ Recording completed: {output_dir}/{filename}")
                
                # Display file info
                filepath = os.path.join(output_dir, filename)
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"  File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")
                    print(f"  Frames recorded: ~{frame_count}")
                    print(f"  Average FPS: {frame_count / duration_seconds:.1f}")
                
                return True
            else:
                print("\n✗ Error stopping recording")
                return False
    
    def record_with_manual_control(self, output_dir="example_videos"):
        """
        Record video with manual start/stop control.
        
        Args:
            output_dir (str): Output directory for video files
        """
        print("Manual Recording Control Example")
        print("-" * 50)
        print("Press Enter to start recording, Enter again to stop")
        
        ensure_directory_exists(output_dir)
        
        with CameraController(camera_index=0) as camera:
            if not camera.initialize_camera():
                print("Error: Could not initialize camera")
                return False
            
            input("Press Enter to start recording...")
            
            # Start recording
            filename = "example_manual_control.mp4"
            
            if not camera.start_recording(filename, output_dir):
                print("Failed to start recording")
                return False
            
            print(f"Recording started: {filename}")
            print("Press Enter to stop recording...")
            
            # Start recording thread
            self.recording_active = True
            recording_thread = threading.Thread(target=self._recording_loop, args=(camera,))
            recording_thread.start()
            
            # Wait for user input to stop
            input()
            
            # Stop recording
            self.recording_active = False
            recording_thread.join()
            
            if camera.stop_recording():
                print(f"✓ Recording stopped and saved: {output_dir}/{filename}")
                
                # Display file info
                filepath = os.path.join(output_dir, filename)
                if os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    print(f"  File size: {file_size:,} bytes ({file_size / (1024*1024):.1f} MB)")
                
                return True
            else:
                print("✗ Error stopping recording")
                return False
    
    def _recording_loop(self, camera):
        """
        Recording loop for manual control example.
        
        Args:
            camera: Camera controller instance
        """
        frame_count = 0
        start_time = time.time()
        
        while self.recording_active:
            if camera.record_frame():
                frame_count += 1
            
            # Show progress every 5 seconds
            current_time = time.time()
            elapsed = current_time - start_time
            if int(elapsed) % 5 == 0 and elapsed > 1:
                print(f"Recording... {int(elapsed)} seconds, ~{frame_count} frames")
                time.sleep(1)  # Avoid multiple prints per second
            
            time.sleep(0.033)  # ~30 FPS
    
    def record_multiple_clips(self, num_clips=3, clip_duration=5, output_dir="example_videos"):
        """
        Record multiple short video clips.
        
        Args:
            num_clips (int): Number of clips to record
            clip_duration (int): Duration of each clip in seconds
            output_dir (str): Output directory for video files
        """
        print(f"Multiple Clips Example: {num_clips} clips of {clip_duration} seconds each")
        print("-" * 50)
        
        ensure_directory_exists(output_dir)
        
        with CameraController(camera_index=0) as camera:
            if not camera.initialize_camera():
                print("Error: Could not initialize camera")
                return False
            
            for clip_num in range(1, num_clips + 1):
                print(f"\nRecording clip {clip_num}/{num_clips}...")
                
                filename = f"example_clip_{clip_num}.mp4"
                
                if not camera.start_recording(filename, output_dir):
                    print(f"Failed to start recording clip {clip_num}")
                    continue
                
                # Record clip
                start_time = time.time()
                while time.time() - start_time < clip_duration:
                    camera.record_frame()
                    time.sleep(0.033)
                
                # Stop recording
                if camera.stop_recording():
                    print(f"✓ Clip {clip_num} saved: {filename}")
                else:
                    print(f"✗ Error saving clip {clip_num}")
                
                # Brief pause between clips
                if clip_num < num_clips:
                    print("Pausing for 2 seconds...")
                    time.sleep(2)
            
            print(f"\n✓ All clips saved to: {os.path.abspath(output_dir)}")
            return True


def main():
    """Main function demonstrating video recording examples."""
    print("Video Recording Examples")
    print("=" * 40)
    
    example = VideoRecordingExample()
    
    try:
        # Example 1: Record for specific duration
        print("\n1. Recording for 5 seconds...")
        if not example.record_with_duration(5):
            print("Example 1 failed")
            return False
        
        time.sleep(2)  # Brief pause
        
        # Example 2: Multiple short clips
        print("\n2. Recording 3 short clips (3 seconds each)...")
        if not example.record_multiple_clips(3, 3):
            print("Example 2 failed")
            return False
        
        # Example 3: Manual control (commented out for automated testing)
        # print("\n3. Manual recording control...")
        # if not example.record_with_manual_control():
        #     print("Example 3 failed")
        #     return False
        
        print("\n✓ All video recording examples completed successfully!")
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
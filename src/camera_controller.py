"""
Camera Controller Module

This module provides a CameraController class for managing USB webcam operations
including initialization, photo capture, video recording, and resource cleanup.
"""

import cv2
import numpy as np
import time
from datetime import datetime
import os
import sys
import glob
from typing import Optional, Tuple, List


class CameraController:
    """
    A controller class for managing USB webcam operations.
    
    This class handles camera initialization, frame capture, photo saving,
    video recording, and proper resource cleanup.
    """
    
    def __init__(self, camera_index: int = 0):
        """
        Initialize the camera controller.
        
        Args:
            camera_index (int): Index of the camera to use (default: 0)
        """
        self.camera_index = camera_index
        self.cap = None
        self.is_recording = False
        self.video_writer = None
        self.recording_filename = None
        
    def initialize_camera(self) -> bool:
        """
        Initialize the camera connection with auto-detection and Linux USB fixes.
        
        Returns:
            bool: True if camera initialized successfully, False otherwise
        """
        if sys.platform.startswith("linux"):
            device_indices = self._get_linux_device_indices()
            if not device_indices:
                print("No /dev/video* devices found")
                return False
        return self._try_initialize_with_backends([self.camera_index])

    def _get_linux_device_indices(self) -> List[int]:
        """Return available /dev/video* indices on Linux."""
        device_indices = []
        for path in glob.glob("/dev/video*"):
            name = os.path.basename(path)
            suffix = name.replace("video", "")
            if suffix.isdigit():
                device_indices.append(int(suffix))
        return sorted(set(device_indices))
    
    def _try_initialize_with_backends(self, camera_indices):
        """
        Try initializing camera with different backends to fix Linux USB issues.
        
        Args:
            camera_indices: List of camera indices to try
            
        Returns:
            bool: True if successful
        """
        # Different backends to try for Linux USB webcam compatibility
        backends_to_try = [
            cv2.CAP_V4L2,    # Video4Linux2 - most common on Linux
            cv2.CAP_V4L,     # Video4Linux - fallback
            cv2.CAP_ANY,     # Auto-detect backend
            cv2.CAP_GSTREAMER  # GStreamer - alternative
        ]
        
        for camera_index in camera_indices:
            for backend in backends_to_try:
                try:
                    print(f"Trying camera {camera_index} with backend {self._get_backend_name(backend)}...")
                    
                    # Create VideoCapture with specific backend
                    self.cap = cv2.VideoCapture(camera_index, backend)
                    if not self.cap.isOpened():
                        continue
                    
                    # Apply Linux USB webcam fixes before testing
                    success = self._apply_usb_webcam_fixes()
                    if not success:
                        self.cap.release()
                        continue
                    
                    # Test frame capture with multiple attempts
                    frame_captured = False
                    for attempt in range(5):  # Try multiple times
                        ret, frame = self.cap.read()
                        if ret and frame is not None and frame.size > 0:
                            # Check if frame is not just black
                            if frame.mean() > 1.0:  # Not completely black
                                frame_captured = True
                                break
                        time.sleep(0.1)  # Small delay between attempts
                    
                    if frame_captured:
                        print(f"Successfully initialized camera {camera_index} with {self._get_backend_name(backend)}")
                        self.camera_index = camera_index
                        self._configure_camera_properties()
                        return True
                    else:
                        print(f"Camera {camera_index} with {self._get_backend_name(backend)} opened but produces black frames")
                        self.cap.release()
                        
                except Exception as e:
                    print(f"Error with camera {camera_index}, backend {self._get_backend_name(backend)}: {e}")
                    if hasattr(self, 'cap') and self.cap:
                        self.cap.release()
        
        # If specific indices fail, try auto-detection
        if camera_indices == [self.camera_index]:
            print("Specified camera failed, searching for available cameras...")
            available_cameras = self.list_available_cameras()
            if available_cameras and available_cameras != [self.camera_index]:
                return self._try_initialize_with_backends(available_cameras)
        
        print("No working cameras found with any backend")
        return False
    
    def _get_backend_name(self, backend):
        """Get human-readable backend name."""
        backend_names = {
            cv2.CAP_V4L2: "V4L2",
            cv2.CAP_V4L: "V4L", 
            cv2.CAP_ANY: "AUTO",
            cv2.CAP_GSTREAMER: "GStreamer"
        }
        return backend_names.get(backend, f"Backend_{backend}")
    
    def _apply_usb_webcam_fixes(self):
        """
        Apply various fixes for USB webcam issues on Linux.
        
        Returns:
            bool: True if fixes applied successfully
        """
        if not self.cap or not self.cap.isOpened():
            return False
        
        try:
            # Fix 1: Set buffer size to reduce latency and potential black frames
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Fix 2: Force specific pixel format (MJPG is often more reliable)
            # Try MJPG first as it's widely supported and efficient
            self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
            
            # Fix 3: Set reasonable resolution (many USB cams have issues with high res)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Fix 4: Set stable framerate
            self.cap.set(cv2.CAP_PROP_FPS, 15)
            
            # Fix 5: Disable auto-exposure initially (can cause black frames)
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # Manual mode
            
            # Fix 6: Set reasonable exposure value
            self.cap.set(cv2.CAP_PROP_EXPOSURE, -5)
            
            # Fix 7: Enable auto white balance
            self.cap.set(cv2.CAP_PROP_AUTO_WB, 1)
            
            # Fix 8: Flush initial frames that might be black
            for _ in range(5):
                self.cap.read()
                
            time.sleep(0.2)  # Give camera time to adjust
            
            return True
            
        except Exception as e:
            print(f"Error applying USB webcam fixes: {e}")
            return False
    
    def _configure_camera_properties(self):
        """Configure camera properties for better quality."""
        if self.cap and self.cap.isOpened():
            # Set camera properties for better quality
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Get actual values (cameras may not support all settings)
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            print(f"Camera configured: {width}x{height} @ {fps:.1f}FPS")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera with black frame detection.
        
        Returns:
            np.ndarray: Captured frame as numpy array, or None if failed
        """
        if not self.cap or not self.cap.isOpened():
            return None
        
        # Try multiple attempts to get a non-black frame
        max_attempts = 10
        for attempt in range(max_attempts):
            ret, frame = self.cap.read()
            if ret and frame is not None and frame.size > 0:
                # Check if frame is not completely black
                frame_mean = frame.mean()
                if frame_mean > 1.0:  # Not a black frame
                    return frame
                elif attempt < max_attempts - 1:  # Not the last attempt
                    # Skip this black frame and try again
                    time.sleep(0.05)
                    continue
                else:
                    # Last attempt - return even if black (better than None)
                    print("Warning: Camera producing black frames")
                    return frame
            elif attempt < max_attempts - 1:
                time.sleep(0.05)
        
        return None
    
    # TODO Allow user to specify filename based on batch
    # TODO Allow user to specify exposure time and gain
    def take_photo(self, filename: Optional[str] = None, output_dir: str = "photos") -> bool:
        """
        Capture and save a photo.
        
        Args:
            filename (str, optional): Custom filename for the photo
            output_dir (str): Directory to save photos (default: "photos")
            
        Returns:
            bool: True if photo saved successfully, False otherwise
        """
        frame = self.get_frame()
        if frame is None:
            return False
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp if not provided
        if filename is None:
            # TODO if doing timestamp, reduce unnecessary variables
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{timestamp}.jpg"
        
        filepath = os.path.join(output_dir, filename)
        
        try:
            cv2.imwrite(filepath, frame)
            print(f"Photo saved: {filepath}")
            return True
        except Exception as e:
            print(f"Error saving photo: {e}")
            return False
    
    def start_recording(self, filename: Optional[str] = None, output_dir: str = "videos") -> bool:
        """
        Start video recording.
        
        Args:
            filename (str, optional): Custom filename for the video
            output_dir (str): Directory to save videos (default: "videos")
            
        Returns:
            bool: True if recording started successfully, False otherwise
        """
        if self.is_recording:
            print("Already recording!")
            return False
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp if not provided
        if filename is None:
            # TODO if doing timestamp, reduce unnecessary variables
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_{timestamp}.mp4"
        
        self.recording_filename = os.path.join(output_dir, filename)
        
        # Get camera properties
        fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Initialize video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            self.recording_filename, fourcc, fps, (width, height)
        )
        
        if not self.video_writer.isOpened():
            print("Error: Could not initialize video writer")
            return False
        
        self.is_recording = True
        print(f"Recording started: {self.recording_filename}")
        return True
    
    def record_frame(self) -> bool:
        """
        Record the current frame to video (call this continuously while recording).
        
        Returns:
            bool: True if frame recorded successfully, False otherwise
        """
        if not self.is_recording or not self.video_writer:
            return False
        
        frame = self.get_frame()
        if frame is not None:
            self.video_writer.write(frame)
            return True
        return False
    
    def stop_recording(self) -> bool:
        """
        Stop video recording and save the file.
        
        Returns:
            bool: True if recording stopped successfully, False otherwise
        """
        if not self.is_recording:
            return False
        
        self.is_recording = False
        
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
            print(f"Recording saved: {self.recording_filename}")
            return True
        
        return False
    
    def get_camera_properties(self) -> dict:
        """
        Get current camera properties.
        
        Returns:
            dict: Dictionary containing camera properties
        """
        if not self.cap or not self.cap.isOpened():
            return {}
        
        properties = {
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': int(self.cap.get(cv2.CAP_PROP_FPS)),
            'brightness': self.cap.get(cv2.CAP_PROP_BRIGHTNESS),
            'contrast': self.cap.get(cv2.CAP_PROP_CONTRAST),
            'saturation': self.cap.get(cv2.CAP_PROP_SATURATION),
            'exposure': self.cap.get(cv2.CAP_PROP_EXPOSURE),
            'gain': self.cap.get(cv2.CAP_PROP_GAIN),
            'auto_exposure': self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE),
        }
        return properties
    
    def set_camera_property(self, property_id: int, value: float) -> bool:
        """
        Set a camera property.
        
        Args:
            property_id (int): OpenCV property identifier
            value (float): Value to set
            
        Returns:
            bool: True if property set successfully, False otherwise
        """
        if not self.cap or not self.cap.isOpened():
            return False
        
        return self.cap.set(property_id, value)
    
    def set_exposure_time(self, exposure_value: float) -> bool:
        """
        Set camera exposure time.
        
        Args:
            exposure_value (float): Exposure value in camera-specific units
            
        Returns:
            bool: True if exposure set successfully, False otherwise
        """
        if not self.cap or not self.cap.isOpened():
            return False
        
        # V4L2 cameras use mode 1 for manual exposure (not 0.25)
        # Try both common manual modes
        auto_mode = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        if auto_mode != 1.0 and auto_mode != 0.25:
            # Try V4L2 manual mode first
            if not self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1):
                # Fall back to OpenCV mode
                self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
        
        # Set the exposure value
        return self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure_value)
    
    def set_gain(self, gain_value: float) -> bool:
        """
        Set camera gain.
        
        Args:
            gain_value (float): Gain value (typically 0-100, camera dependent)
            
        Returns:
            bool: True if gain set successfully, False otherwise
        """
        if not self.cap or not self.cap.isOpened():
            return False
        
        return self.cap.set(cv2.CAP_PROP_GAIN, gain_value)
    
    def set_auto_exposure(self, auto: bool) -> bool:
        """
        Enable or disable auto exposure.
        
        Args:
            auto (bool): True to enable auto exposure, False to disable
            
        Returns:
            bool: True if setting was successful, False otherwise
        """
        if not self.cap or not self.cap.isOpened():
            return False
        
        # V4L2 cameras: 3 = auto, 1 = manual
        # OpenCV default: 0.75 = auto, 0.25 = manual
        # Try V4L2 mode first, fall back to OpenCV mode
        if auto:
            return self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 3) or \
                   self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75)
        else:
            return self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) or \
                   self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)
    
    def get_exposure_range(self) -> Tuple[float, float]:
        """
        Get the supported exposure range for this camera.
        
        Returns:
            Tuple[float, float]: (min_exposure, max_exposure) or (0, 0) if not supported
        """
        if not self.cap or not self.cap.isOpened():
            return (0.0, 0.0)
        
        # Try to probe the actual exposure range
        # First ensure manual mode
        original_mode = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # V4L2 manual
        
        # Get current exposure as a reference
        current = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        
        # Try to find min/max by testing values
        self.cap.set(cv2.CAP_PROP_EXPOSURE, 1)
        min_exp = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        
        self.cap.set(cv2.CAP_PROP_EXPOSURE, 10000)
        max_exp = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        
        # Restore original exposure and mode
        self.cap.set(cv2.CAP_PROP_EXPOSURE, current)
        self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, original_mode)
        
        return (min_exp, max_exp)
    
    def get_gain_range(self) -> Tuple[float, float]:
        """
        Get the supported gain range for this camera.
        
        Returns:
            Tuple[float, float]: (min_gain, max_gain) or (0, 0) if not supported
        """
        if not self.cap or not self.cap.isOpened():
            return (0.0, 0.0)
        
        # Try to get gain range - this is camera dependent
        # Most USB cameras support gain values between 0 and 100
        try:
            current_gain = self.cap.get(cv2.CAP_PROP_GAIN)
            # Return a reasonable default range for USB cameras
            return (0.0, 100.0)
        except:
            return (0.0, 0.0)
    
    def capture_timelapse_series(self, num_photos: int, interval_seconds: float, 
                               output_dir: str = "timelapse", 
                               base_filename: str = None,
                               exposure: float = None, gain: float = None, 
                               auto_exposure: bool = None,
                               progress_callback=None) -> List[str]:
        """
        Capture a series of photos with consistent settings at regular intervals.
        
        Args:
            num_photos (int): Number of photos to capture
            interval_seconds (float): Time interval between photos in seconds
            output_dir (str): Directory to save photos
            base_filename (str, optional): Base filename (will add sequence numbers)
            exposure (float, optional): Fixed exposure setting for all photos
            gain (float, optional): Fixed gain setting for all photos
            auto_exposure (bool, optional): Auto exposure setting
            progress_callback (callable, optional): Callback function for progress updates
            
        Returns:
            List[str]: List of captured photo filenames
        """
        import time
        
        if not self.cap or not self.cap.isOpened():
            print("Camera not initialized")
            return []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Apply camera settings once for consistency
        if auto_exposure is not None:
            self.set_auto_exposure(auto_exposure)
            time.sleep(0.5)  # Allow camera to adjust
        
        if exposure is not None and not auto_exposure:
            self.set_exposure_time(exposure)
            time.sleep(0.5)
        
        if gain is not None:
            self.set_gain(gain)
            time.sleep(0.5)
        
        captured_files = []
        
        # Generate base filename if not provided
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"timelapse_{timestamp}"
        
        print(f"Starting timelapse: {num_photos} photos, {interval_seconds}s intervals")
        print(f"Saving to: {output_dir}")
        
        for i in range(num_photos):
            # Generate filename with sequence number
            filename = f"{base_filename}_{i+1:04d}.jpg"
            filepath = os.path.join(output_dir, filename)
            
            # Capture photo
            frame = self.get_frame()
            if frame is not None:
                try:
                    success = cv2.imwrite(filepath, frame)
                    if success:
                        captured_files.append(filename)
                        print(f"Captured {i+1}/{num_photos}: {filename}")
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(i + 1, num_photos, filename)
                    else:
                        print(f"Failed to save photo {i+1}/{num_photos}")
                except Exception as e:
                    print(f"Error saving photo {i+1}/{num_photos}: {e}")
            else:
                print(f"Failed to capture frame {i+1}/{num_photos}")
            
            # Wait for next capture (except on last photo)
            if i < num_photos - 1:
                print(f"Waiting {interval_seconds}s for next capture...")
                time.sleep(interval_seconds)
        
        print(f"Timelapse complete! Captured {len(captured_files)}/{num_photos} photos")
        return captured_files
    
    def list_available_cameras(self, verbose=True) -> List[int]:
        """
        List all available camera indices with validation.
        
        Args:
            verbose: Whether to print status messages
        
        Returns:
            List[int]: List of available and working camera indices
        """
        available_cameras = []

        if sys.platform.startswith("linux"):
            device_indices = self._get_linux_device_indices()
        else:
            device_indices = list(range(16))

        # Check camera indices from detected device nodes (or fallback range)
        for i in device_indices:
            try:
                if sys.platform.startswith("linux"):
                    cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
                else:
                    cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Actually test if we can read a frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        available_cameras.append(i)
                        if verbose:
                            print(f"Found working camera at index {i}")
                    elif verbose:
                        print(f"Camera at index {i} opened but cannot read frames")
                    cap.release()
            except Exception as e:
                # Silently continue if there's an error with this index
                pass
        
        return available_cameras
    
    def get_camera_info(self, camera_index=None):
        """
        Get detailed information about a camera.
        
        Args:
            camera_index: Camera index to check, or None for current camera
            
        Returns:
            dict: Camera information including resolution, FPS, etc.
        """
        if camera_index is None:
            camera_index = self.camera_index
            
        info = {
            'index': camera_index,
            'available': False,
            'width': None,
            'height': None,
            'fps': None,
            'backend': None
        }
        
        try:
            # Use temporary capture if not checking current camera
            if camera_index == self.camera_index and self.cap and self.cap.isOpened():
                cap = self.cap
                temp_cap = False
            else:
                cap = cv2.VideoCapture(camera_index)
                temp_cap = True
            
            if cap.isOpened():
                ret, frame = cap.read()
                if ret and frame is not None:
                    info['available'] = True
                    info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    info['fps'] = cap.get(cv2.CAP_PROP_FPS)
                    info['backend'] = cap.get(cv2.CAP_PROP_BACKEND)
            
            if temp_cap:
                cap.release()
                
        except Exception as e:
            print(f"Error getting camera info for index {camera_index}: {e}")
        
        return info
    
    def check_camera_health(self):
        """
        Check if camera is producing valid frames.
        
        Returns:
            bool: True if camera is healthy, False if producing black/invalid frames
        """
        if not self.cap or not self.cap.isOpened():
            return False
        
        # Test multiple frames to check consistency
        black_frame_count = 0
        total_checks = 5
        
        for _ in range(total_checks):
            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
                black_frame_count += 1
            elif frame.mean() <= 1.0:  # Very dark/black frame
                black_frame_count += 1
            time.sleep(0.1)
        
        # If more than half the frames are black/invalid, camera is unhealthy
        return black_frame_count < (total_checks / 2)
    
    def reinitialize_camera(self):
        """
        Reinitialize camera if experiencing issues like black frames.
        
        Returns:
            bool: True if reinitialization successful
        """
        print("Reinitializing camera due to issues...")
        current_index = self.camera_index
        
        # Release current camera
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Wait a moment for camera to be released
        time.sleep(0.5)
        
        # Reinitialize
        self.camera_index = current_index
        return self.initialize_camera()
    
    def release(self):
        """
        Release camera resources and cleanup.
        """
        if self.is_recording:
            self.stop_recording()
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        cv2.destroyAllWindows()
        print("Camera resources released")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize_camera()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
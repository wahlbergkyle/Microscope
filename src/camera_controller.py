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
import threading
from typing import Optional, Tuple, List
import warnings
import contextlib

# Suppress Python warnings
warnings.filterwarnings('ignore')

# Suppress OpenCV error messages on Windows (especially obsensor errors)
if sys.platform.startswith('win'):
    os.environ['OPENCV_LOG_LEVEL'] = 'FATAL'  # Only show fatal errors
    os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'  # Deprioritize MSMF
    os.environ['OPENCV_VIDEOIO_PRIORITY_DSHOW'] = '100'  # Prioritize DirectShow


# Helper context manager to suppress stderr on Windows
@contextlib.contextmanager
def suppress_opencv_warnings():
    """Suppress OpenCV warnings by redirecting stderr."""
    if sys.platform.startswith('win'):
        import msvcrt
        stderr_fileno = sys.stderr.fileno()
        old_stderr = os.dup(stderr_fileno)
        devnull = os.open(os.devnull, os.O_WRONLY)
        try:
            os.dup2(devnull, stderr_fileno)
            yield
        finally:
            os.dup2(old_stderr, stderr_fileno)
            os.close(devnull)
            os.close(old_stderr)
    else:
        yield


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
        self.auto_exposure_enabled = None
        self._lock = threading.RLock()  # Reentrant: range probing calls set_auto_exposure
        
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
        Try initializing camera with different backends based on platform.
        
        Args:
            camera_indices: List of camera indices to try
            
        Returns:
            bool: True if successful
        """
        # Platform-specific backends to try
        if sys.platform.startswith('win'):
            # Windows: Try DirectShow first, then MSMF as fallback
            backends_to_try = [
                cv2.CAP_DSHOW,   # DirectShow - most reliable for most cameras
                cv2.CAP_MSMF,    # Windows Media Foundation - works for some cameras
                cv2.CAP_ANY,     # Auto-detect backend (fallback)
            ]
        elif sys.platform.startswith('linux'):
            # Linux: Use V4L2/V4L
            backends_to_try = [
                cv2.CAP_V4L2,    # Video4Linux2 - most common on Linux
                cv2.CAP_V4L,     # Video4Linux - fallback
                cv2.CAP_ANY,     # Auto-detect backend
                cv2.CAP_GSTREAMER  # GStreamer - alternative
            ]
        elif sys.platform.startswith('darwin'):
            # macOS: Use AVFoundation
            backends_to_try = [
                cv2.CAP_AVFOUNDATION,  # AVFoundation - macOS native
                cv2.CAP_ANY,           # Auto-detect backend
            ]
        else:
            # Unknown platform: just try auto-detect
            backends_to_try = [cv2.CAP_ANY]
        
        for camera_index in camera_indices:
            for backend in backends_to_try:
                try:
                    print(f"Trying camera {camera_index} with backend {self._get_backend_name(backend)}...")
                    
                    # Create VideoCapture with specific backend
                    self.cap = cv2.VideoCapture(camera_index, backend)
                    if not self.cap.isOpened():
                        continue
                    
                    # Apply platform-specific webcam fixes before testing
                    if sys.platform.startswith('linux'):
                        success = self._apply_usb_webcam_fixes()
                        if not success:
                            self.cap.release()
                            continue
                    
                    # Test frame capture with multiple attempts
                    # DirectShow on Windows may produce black frames initially - give it more time
                    max_test_attempts = 30 if (sys.platform.startswith('win') and backend == cv2.CAP_DSHOW) else 5
                    warmup_delay = 0.2 if (sys.platform.startswith('win') and backend == cv2.CAP_DSHOW) else 0.1
                    
                    frame_captured = False
                    for attempt in range(max_test_attempts):
                        ret, frame = self.cap.read()
                        if ret and frame is not None and frame.size > 0:
                            # Check if frame is not just black
                            if frame.mean() > 1.0:  # Not completely black
                                frame_captured = True
                                break
                        time.sleep(warmup_delay)
                    
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
            cv2.CAP_GSTREAMER: "GStreamer",
            cv2.CAP_DSHOW: "DirectShow",
            cv2.CAP_MSMF: "MSMF",
            cv2.CAP_AVFOUNDATION: "AVFoundation"
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
            
            # Fix 4: DON'T limit FPS - let camera run at native speed
            # Setting low FPS here can throttle recording performance
            
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
            self.auto_exposure_enabled = self._infer_auto_exposure_state()
            
            print(f"Camera configured: {width}x{height} @ {fps:.1f}FPS")

    def _switch_camera_backend(self, backend: int) -> bool:
        """Reopen current camera with a different backend."""
        old_backend = None
        try:
            if self.cap and self.cap.isOpened():
                old_backend = int(self.cap.get(cv2.CAP_PROP_BACKEND))
        except Exception:
            old_backend = None

        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass

        try:
            print(f"Trying to reopen camera {self.camera_index} with backend {self._get_backend_name(backend)}...")
            new_cap = cv2.VideoCapture(self.camera_index, backend)
            if not new_cap.isOpened():
                return False

            frame_ok = False
            for _ in range(12):
                ret, frame = new_cap.read()
                if ret and frame is not None and frame.size > 0:
                    frame_ok = True
                    break
                time.sleep(0.05)

            if not frame_ok:
                new_cap.release()
                return False

            self.cap = new_cap
            self._configure_camera_properties()
            return True
        except Exception as error:
            print(f"Failed to switch backend: {error}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        Capture a single frame from the camera with black frame detection.
        
        Returns:
            np.ndarray: Captured frame as numpy array, or None if failed
        """
        if not self.cap or not self.cap.isOpened():
            print("get_frame: Camera not opened")
            return None
        
        # Try multiple attempts to get a non-black frame
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                with self._lock:
                    ret, frame = self.cap.read()
                if not ret:
                    if attempt == 0:
                        print(f"get_frame: cap.read() returned False")
                if ret and frame is not None and frame.size > 0:
                    # Ensure frame is contiguous in memory (fixes Windows MSMF issues)
                    # This MUST be done before any operations on the frame
                    if not frame.flags['C_CONTIGUOUS']:
                        frame = np.ascontiguousarray(frame)
                    
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
            except (cv2.error, ValueError) as e:
                # Handle OpenCV matrix errors on Windows (MSMF stride issues)
                if attempt == 0:
                    print(f"get_frame: Error on read - {type(e).__name__}: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(0.05)
                    continue
                else:
                    print(f"Camera frame error after {max_attempts} attempts: {e}")
                    return None
            
            if attempt < max_attempts - 1:
                time.sleep(0.05)
        
        return None
    
    # TODO Allow user to specify filename based on batch
    # TODO Allow user to specify exposure time and gain
    def take_photo(self, filename: Optional[str] = None, output_dir: str = "photos") -> tuple[bool, Optional[np.ndarray]]:
        """
        Capture and save a photo.
        
        Args:
            filename (str, optional): Custom filename for the photo
            output_dir (str): Directory to save photos (default: "photos")
            
        Returns:
            tuple: (success: bool, frame: np.ndarray or None) - True/frame if photo saved successfully
        """
        frame = self.get_frame()
        if frame is None:
            return False, None
        
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
            return True, frame
        except Exception as e:
            print(f"Error saving photo: {e}")
            return False, None
    
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
            filename = f"video_{timestamp}.mp4"  # Use .mp4 for best compatibility
        
        # Ensure .mp4 extension
        base_name = os.path.splitext(filename)[0]
        
        self.recording_filename = os.path.join(output_dir, base_name + ".mp4")
        
        # Measure the camera's ACTUAL frame delivery rate.
        # Many cameras (especially via DirectShow) report an incorrect FPS
        # through CAP_PROP_FPS.  Using the reported value causes the video
        # to play back at the wrong speed.  Instead, we time a short burst
        # of real cap.read() calls to get the true rate.
        reported_fps = int(self.cap.get(cv2.CAP_PROP_FPS))
        measured_fps = self._measure_actual_fps()
        writer_fps = measured_fps
        print(f"Camera reports {reported_fps} FPS, measured {measured_fps} FPS, using {writer_fps} FPS for video file")
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Ensure dimensions are even (required for many codecs)
        width = width - (width % 2)
        height = height - (height % 2)
        
        print(f"Recording settings: {width}x{height} @ {writer_fps} FPS")
        
        # Store dimensions for frame validation
        self.recording_width = width
        self.recording_height = height
        
        # Platform-specific codec selection
        if sys.platform.startswith('win'):
            codecs_to_try = [
                ('mp4v', 'MPEG-4 (mp4v)'),     # Proper MP4 codec
                ('MP4V', 'MPEG-4 (MP4V)'),     # Uppercase variant
                ('XVID', 'XVID'),               # Compatible fallback
            ]
        else:
            codecs_to_try = [
                ('mp4v', 'MPEG-4'),
                ('avc1', 'H264'),
                ('X264', 'X264'),
                ('XVID', 'XVID'),
            ]
        
        self.video_writer = None
        for fourcc_code, codec_name in codecs_to_try:
            try:
                fourcc = cv2.VideoWriter_fourcc(*fourcc_code)
                # Create VideoWriter with the conservative FPS we can achieve
                writer = cv2.VideoWriter(
                    self.recording_filename, 
                    fourcc,  # Don't force FFmpeg backend - let OpenCV choose
                    writer_fps,  # Use realistic FPS
                    (width, height),
                    True  # isColor flag
                )
                # Test if it actually works
                if writer.isOpened():
                    self.video_writer = writer
                    self.video_codec = fourcc_code  # Store for debugging
                    print(f"Using {codec_name} codec for .mp4 recording")
                    break
                else:
                    writer.release()
            except Exception as e:
                pass  # Try next codec
        
        if not self.video_writer or not self.video_writer.isOpened():
            # Fallback: try MJPG in .avi container (MJPG doesn't work in .mp4)
            try:
                avi_filename = os.path.splitext(self.recording_filename)[0] + '.avi'
                fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                writer = cv2.VideoWriter(avi_filename, fourcc, writer_fps,
                                        (width, height), True)
                if writer.isOpened():
                    self.video_writer = writer
                    self.video_codec = 'MJPG'
                    self.recording_filename = avi_filename
                    print(f"Using Motion JPEG codec in .avi container")
                else:
                    writer.release()
            except Exception:
                pass

        if not self.video_writer or not self.video_writer.isOpened():
            print("Error: Could not initialize video writer with any codec")
            return False
        
        # Minimize buffer to reduce latency
        try:
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        except Exception as e:
            print(f"Note: Could not set buffer size: {e}")
        
        self.is_recording = True
        self.frame_count = 0  # Track frames written
        self.recording_start_time = time.time()  # Track when recording started
        print(f"Recording started: {self.recording_filename}")
        
        return True
    
    def _measure_actual_fps(self, sample_frames: int = 15) -> int:
        """
        Measure the camera's actual frame delivery rate by timing real reads.
        
        Args:
            sample_frames: Number of frames to time (more = more accurate but slower).
        
        Returns:
            int: Measured FPS, clamped to a sensible range (5-120).
        """
        if not self.cap or not self.cap.isOpened():
            return 10  # Safe default
        
        try:
            # Warm up: discard a couple of frames to let the pipeline stabilize
            with self._lock:
                for _ in range(3):
                    self.cap.read()
            
            # Time the burst
            with self._lock:
                start = time.time()
                good = 0
                for _ in range(sample_frames):
                    ret, _ = self.cap.read()
                    if ret:
                        good += 1
                elapsed = time.time() - start
            
            if good < 3 or elapsed <= 0:
                return 10  # Not enough data
            
            fps = good / elapsed
            # Clamp to a sensible range and round to nearest integer
            fps = max(5, min(120, round(fps)))
            return fps
        except Exception as e:
            print(f"FPS measurement failed: {e}")
            return 10

    def record_frame(self) -> tuple[bool, Optional[np.ndarray]]:
        """
        Record the current frame to video (call this continuously while recording).
        Uses fast path optimized for video - bypasses get_frame() overhead.
        
        Returns:
            tuple: (success: bool, frame: np.ndarray or None) - True/frame if recorded successfully
        """
        if not self.is_recording or not self.video_writer:
            return False, None
        
        if not self.cap or not self.cap.isOpened():
            return False, None
        
        try:
            # Fast path: direct read without validation overhead
            with self._lock:
                ret, frame = self.cap.read()
            
            if ret and frame is not None and frame.size > 0:
                # Resize frame if needed to match recording dimensions
                if hasattr(self, 'recording_width') and hasattr(self, 'recording_height'):
                    if frame.shape[1] != self.recording_width or frame.shape[0] != self.recording_height:
                        frame = cv2.resize(frame, (self.recording_width, self.recording_height))
                
                # Write immediately - no black frame detection, no retries
                if self.is_recording and self.video_writer:
                    try:
                        self.video_writer.write(frame)
                        if hasattr(self, 'frame_count'):
                            self.frame_count += 1
                        return True, frame
                    except Exception as write_error:
                        print(f"Error writing frame {self.frame_count}: {write_error}")
                        return False, None
                    
        except (cv2.error, Exception) as e:
            # Log but don't retry - keep going for video
            if self.is_recording:
                print(f"Error capturing frame: {e}")
            return False, None
            
        return False, None
    
    def stop_recording(self) -> bool:
        """
        Stop video recording and save the file.
        
        Returns:
            bool: True if recording stopped successfully, False otherwise
        """
        if not self.is_recording:
            return False
        
        self.is_recording = False
        
        # Small delay to allow recording thread to finish current frame
        import time
        time.sleep(0.15)
        
        if self.video_writer:
            # Print stats before closing
            frame_count = getattr(self, 'frame_count', 0)
            recording_duration = time.time() - getattr(self, 'recording_start_time', time.time())
            actual_fps = frame_count / recording_duration if recording_duration > 0 else 0
            
            print(f"Finalizing video: {frame_count} frames written over {recording_duration:.1f} seconds")
            print(f"Actual capture rate: {actual_fps:.1f} FPS")
            
            # CRITICAL: Properly finalize the video file
            try:
                # Explicitly flush any buffered frames before release
                # This is critical for MP4 file integrity
                if hasattr(self.video_writer, 'release'):
                    # Give VideoWriter time to finalize internal buffers
                    time.sleep(0.1)
                    
                    # Release the writer - this writes MP4 header and index
                    self.video_writer.release()
                    
                    # Additional delay to ensure file system writes complete
                    time.sleep(0.2)
                    
                    print("Video writer released successfully")
            except Exception as e:
                print(f"Error releasing video writer: {e}")
            finally:
                self.video_writer = None
            
            # Verify the file was created and has size
            if os.path.exists(self.recording_filename):
                file_size = os.path.getsize(self.recording_filename)
                print(f"Recording saved: {self.recording_filename} ({file_size} bytes, {frame_count} frames)")
                
                if file_size < 1000:  # Less than 1KB is suspicious
                    print("Warning: Video file is very small, may be corrupted")
                    print("This usually means the codec failed to initialize properly.")
                elif frame_count == 0:
                    print("Warning: No frames were written to the video file")
                else:
                    print("✓ Video file appears valid")
            else:
                print(f"Warning: Video file not found: {self.recording_filename}")
            
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

    def _is_mode_close(self, value: float, target: float, tolerance: float = 0.05) -> bool:
        """Return True if two mode values are effectively equal."""
        try:
            return abs(float(value) - float(target)) <= tolerance
        except Exception:
            return False

    def _is_known_auto_mode(self, mode_value: float) -> bool:
        """Return True for known auto-exposure mode values."""
        return self._is_mode_close(mode_value, 3.0) or self._is_mode_close(mode_value, 0.75)

    def _is_known_manual_mode(self, mode_value: float) -> bool:
        """Return True for known manual-exposure mode values."""
        return self._is_mode_close(mode_value, 1.0) or self._is_mode_close(mode_value, 0.25) or self._is_mode_close(mode_value, 0.0)

    def _infer_auto_exposure_state(self) -> Optional[bool]:
        """Infer auto exposure state from camera-reported mode values."""
        if not self.cap or not self.cap.isOpened():
            return None

        mode_value = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        if self._is_known_auto_mode(mode_value):
            return True
        if self._is_known_manual_mode(mode_value):
            return False
        return None

    def is_auto_exposure_enabled(self, default: bool = True) -> bool:
        """Return current auto exposure state with fallback for ambiguous drivers."""
        if self.auto_exposure_enabled is not None:
            return self.auto_exposure_enabled

        inferred = self._infer_auto_exposure_state()
        if inferred is not None:
            self.auto_exposure_enabled = inferred
            return inferred

        return default

    def _probe_manual_exposure_control(self) -> bool:
        """Check if manual exposure control is effective even with ambiguous auto-mode values."""
        if not self.cap or not self.cap.isOpened():
            return False

        original_exposure = self.cap.get(cv2.CAP_PROP_EXPOSURE)
        # Wide sweep covers V4L2 log2 scale (-13..-1), mid-range, and high
        # absolute values so cameras on any driver scale are detected.
        probe_values = [-13.0, -7.0, -1.0, 1.0, 16.0, 256.0, 4096.0, 65536.0]
        observed_values = []

        try:
            for value in probe_values:
                self.cap.set(cv2.CAP_PROP_EXPOSURE, value)
                time.sleep(0.05)  # Allow driver to latch the new value
                observed = self.cap.get(cv2.CAP_PROP_EXPOSURE)
                observed_float = float(observed)
                observed_values.append(round(observed_float, 2))

            unique_values = set(observed_values)
            if len(unique_values) < 2:
                return False

            min_obs = min(observed_values)
            max_obs = max(observed_values)
            span = abs(max_obs - min_obs)

            # Manual control is considered effective if readback changes across
            # probe values and covers a meaningful span.
            return len(unique_values) >= 3 and span >= 1.0
        except Exception:
            return False
        finally:
            try:
                self.cap.set(cv2.CAP_PROP_EXPOSURE, original_exposure)
            except Exception:
                pass

    def is_manual_exposure_effective(self) -> bool:
        """Public helper to check whether manual exposure control is currently effective."""
        return self._probe_manual_exposure_control()
    
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
        
        # Block manual writes only when we *know* auto exposure is active.
        # Trust self.auto_exposure_enabled over raw driver readback because many
        # DirectShow drivers report stale/incorrect auto-mode values even after
        # a successful switch to manual mode (the probe fallback in
        # set_auto_exposure already accounts for this).
        if self.auto_exposure_enabled is True:
            auto_mode = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            print(f"Warning: Cannot set exposure while in auto exposure mode (mode={auto_mode})")
            print("Hint: Disable auto exposure first before setting manual exposure")
            return False
        
        # Write the exposure value under the lock so the preview thread's
        # cap.read() cannot race with cap.set().
        with self._lock:
            success = self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure_value)

        if success:
            self.auto_exposure_enabled = False
        return success
    
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
        
        # Gain control typically works in both auto and manual modes,
        # but some cameras may ignore it in auto mode
        # We'll allow setting it and let the camera decide
        
        # Set gain under the lock so the preview thread's cap.read()
        # cannot race with cap.set().
        with self._lock:
            success = self.cap.set(cv2.CAP_PROP_GAIN, gain_value)
        
        return success
    
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
        
        # All cap interactions under the lock to prevent race with preview thread.
        with self._lock:
            current_mode = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
            
            # Different cameras use different values for auto/manual modes:
            # Auto modes: 3 (V4L2), 0.75 (DirectShow/OpenCV), -1 (some cameras)
            # Manual modes: 1 (V4L2), 0.25 (DirectShow/OpenCV)
            auto_modes = [3, 0.75, -1]
            manual_modes = [1, 0.25, 0]
            
            # Check if already in the desired mode
            success = False
            if auto:
                if self._is_known_auto_mode(current_mode):
                    success = True
            else:
                if self._is_known_manual_mode(current_mode):
                    success = True

            modes_to_try = auto_modes if auto else manual_modes

            if not success:
                for mode_value in modes_to_try:
                    if self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, mode_value):
                        new_mode = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                        if auto and (self._is_known_auto_mode(new_mode) or self._is_mode_close(new_mode, mode_value)):
                            success = True
                            break
                        elif not auto and (self._is_known_manual_mode(new_mode) or self._is_mode_close(new_mode, mode_value)):
                            success = True
                            break

            if not success:
                # Many DirectShow drivers return ambiguous readback values (e.g. -1)
                # regardless of the actual mode.  Accept optimistically if cap.set
                # returned True for at least one attempt.
                for mode_value in modes_to_try:
                    if self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, mode_value):
                        success = True
                        break

        # Always update the bookkeeping flag — even if the driver gave
        # ambiguous readback, the user’s intent is clear.
        self.auto_exposure_enabled = auto
        
        return success
    
    def get_exposure_range(self) -> Tuple[float, float]:
        """
        Get the supported exposure range for this camera.

        Uses a wide logarithmic probe sweep covering both V4L2 log2 scale
        (-13 to -1) and absolute linear scale (1 to 2^20 ≈ 1,000,000) with a
        per-set settling delay and readback-clamping detection.  Because the
        sweep goes far beyond any commonly assumed limit, the driver's true
        hardware ceiling is reliably discovered even on cameras that support
        much higher exposure values than the typical 10–625 range.

        Returns:
            Tuple[float, float]: (min_exposure, max_exposure) or (0, 0) if not supported
        """
        if not self.cap or not self.cap.isOpened():
            return (0.0, 0.0)

        try:
            with self._lock:
                # Save current state
                original_mode = self.cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
                current = self.cap.get(cv2.CAP_PROP_EXPOSURE)
                original_auto_state = self.auto_exposure_enabled

                # Switch to manual mode so auto-exposure doesn't interfere
                self.set_auto_exposure(False)
                time.sleep(0.1)  # Allow mode-switch to settle

                # Wide probe list:
                #   neg_values  — V4L2 log2 scale: -13, -12, …, -1
                #   pos_values  — exponential steps: 1, 2, 4, …, 1 048 576 (2^20)
                # Exponential steps give good coverage over many orders of
                # magnitude with only ~34 probes total.
                neg_values = list(range(-13, 0))           # -13 … -1
                pos_values = [2**i for i in range(0, 21)]  # 1 … 1 048 576
                test_values = neg_values + pos_values

                # Probe each candidate value.  A 50 ms delay after cap.set() is
                # essential — many drivers need time to latch the value before
                # cap.get() reflects it.
                readbacks: dict = {}
                for val in test_values:
                    self.cap.set(cv2.CAP_PROP_EXPOSURE, float(val))
                    time.sleep(0.05)
                    rb = round(float(self.cap.get(cv2.CAP_PROP_EXPOSURE)), 4)
                    readbacks[float(val)] = rb

                # The true hardware min/max are the extremes of all readback
                # values.  When the driver clamps (e.g. set(1_000_000) reads
                # back 625) the plateau IS the hardware maximum — no extra
                # detection logic needed because we probed well past the limit.
                all_readbacks = list(readbacks.values())
                min_exp = min(all_readbacks)
                max_exp = max(all_readbacks)

                # Restore original exposure and mode
                self.cap.set(cv2.CAP_PROP_EXPOSURE, current)
                time.sleep(0.05)
                if original_auto_state is None:
                    self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, original_mode)
                    self.auto_exposure_enabled = self._infer_auto_exposure_state()
                else:
                    self.set_auto_exposure(original_auto_state)

            # Ensure we have a valid range (min < max)
            if min_exp >= max_exp:
                return (10.0, 625.0)  # Fallback to default

            print(f"Exposure range discovered: {min_exp} to {max_exp}")
            return (min_exp, max_exp)
        except Exception:
            # Fallback to a reasonable default for most webcams
            return (10.0, 625.0)
    
    def get_gain_range(self) -> Tuple[float, float]:
        """
        Get the supported gain range for this camera.
        
        Returns:
            Tuple[float, float]: (min_gain, max_gain) or (0, 0) if not supported
        """
        if not self.cap or not self.cap.isOpened():
            return (0.0, 0.0)
        
        try:
            with self._lock:
                # Save current state (use bookkeeping flag, not raw driver readback)
                current_gain = self.cap.get(cv2.CAP_PROP_GAIN)
                original_auto_state = self.auto_exposure_enabled
                
                # Set manual mode for accurate gain control
                self.set_auto_exposure(False)
                
                # Collect actual values the camera reports
                test_values = [0.0, 0.5, 1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 255.0]
                actual_values = []
                
                for test_val in test_values:
                    self.cap.set(cv2.CAP_PROP_GAIN, test_val)
                    actual = self.cap.get(cv2.CAP_PROP_GAIN)
                    if actual not in actual_values:
                        actual_values.append(actual)
                
                if actual_values:
                    min_gain = min(actual_values)
                    max_gain = max(actual_values)
                else:
                    min_gain, max_gain = 0.0, 100.0  # Fallback
                
                # Restore original state
                self.cap.set(cv2.CAP_PROP_GAIN, current_gain)
                if original_auto_state is None:
                    # State was unknown before probing; re-infer from driver
                    self.auto_exposure_enabled = self._infer_auto_exposure_state()
                else:
                    self.set_auto_exposure(original_auto_state)
            
            # Ensure we have a valid range (min < max)
            if min_gain >= max_gain:
                return (0.0, 100.0)  # Fallback to default
            
            return (min_gain, max_gain)
        except:
            return (0.0, 100.0)  # Fallback to default range
    
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
        elif sys.platform.startswith("win"):
            # On Windows, check fewer indices since most systems have 1-2 cameras
            device_indices = list(range(4))
        else:
            # macOS and others
            device_indices = list(range(8))

        # Check camera indices from detected device nodes (or fallback range)
        for i in device_indices:
            try:
                # Suppress OpenCV errors for unavailable cameras
                with suppress_opencv_warnings():
                    if sys.platform.startswith("linux"):
                        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
                    elif sys.platform.startswith("win"):
                        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                    else:
                        cap = cv2.VideoCapture(i)
                        
                if cap.isOpened():
                    # Actually test if we can read a frame
                    # DirectShow needs warm-up time on Windows
                    try:
                        if sys.platform.startswith("win"):
                            # Give DirectShow time to warm up
                            for _ in range(10):
                                cap.read()
                                time.sleep(0.1)
                        
                        ret, frame = cap.read()
                        if ret and frame is not None and frame.size > 0:
                            available_cameras.append(i)
                            if verbose:
                                print(f"Found working camera at index {i}")
                        elif verbose:
                            print(f"Camera at index {i} opened but cannot read frames")
                    except cv2.error:
                        # Suppress OpenCV errors
                        pass
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
                # Suppress OpenCV backend errors (especially obsensor on Windows)
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    if sys.platform.startswith('win'):
                        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
                    else:
                        cap = cv2.VideoCapture(camera_index)
                temp_cap = True
            
            if cap.isOpened():
                # Try to read frame, but catch matrix assertion errors on Windows
                try:
                    # DirectShow needs warm-up time on Windows
                    if temp_cap and sys.platform.startswith('win'):
                        for _ in range(10):
                            cap.read()
                            time.sleep(0.1)
                    
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0:
                        info['available'] = True
                        info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        info['fps'] = cap.get(cv2.CAP_PROP_FPS)
                        info['backend'] = cap.get(cv2.CAP_PROP_BACKEND)
                except cv2.error:
                    # Suppress OpenCV matrix errors
                    pass
            
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
            self.auto_exposure_enabled = None
        
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
            self.auto_exposure_enabled = None
        
        cv2.destroyAllWindows()
        print("Camera resources released")
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize_camera()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
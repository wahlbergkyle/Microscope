#!/usr/bin/env python3
"""
Test suite for Camera Controller

This module contains unit tests for the CameraController class.
Run with: python -m pytest tests/test_camera.py
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from camera_controller import CameraController


class TestCameraController(unittest.TestCase):
    """Test cases for CameraController class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.camera_controller = CameraController(camera_index=0)
    
    def tearDown(self):
        """Clean up after each test method."""
        if hasattr(self.camera_controller, 'cap') and self.camera_controller.cap:
            self.camera_controller.release()
    
    @patch('camera_controller.cv2.VideoCapture')
    def test_initialize_camera_success(self, mock_video_capture):
        """Test successful camera initialization."""
        # Mock successful camera initialization
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.set.return_value = True
        mock_video_capture.return_value = mock_cap
        
        result = self.camera_controller.initialize_camera()
        
        self.assertTrue(result)
        self.assertEqual(self.camera_controller.cap, mock_cap)
        mock_video_capture.assert_called_once_with(0)
        mock_cap.isOpened.assert_called_once()
    
    @patch('camera_controller.cv2.VideoCapture')
    def test_initialize_camera_failure(self, mock_video_capture):
        """Test failed camera initialization."""
        # Mock failed camera initialization
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        result = self.camera_controller.initialize_camera()
        
        self.assertFalse(result)
        mock_video_capture.assert_called_once_with(0)
        mock_cap.isOpened.assert_called_once()
    
    @patch('camera_controller.cv2.VideoCapture')
    def test_initialize_camera_exception(self, mock_video_capture):
        """Test camera initialization with exception."""
        # Mock exception during initialization
        mock_video_capture.side_effect = Exception("Camera error")
        
        result = self.camera_controller.initialize_camera()
        
        self.assertFalse(result)
    
    def test_get_frame_no_camera(self):
        """Test getting frame when camera is not initialized."""
        result = self.camera_controller.get_frame()
        
        self.assertIsNone(result)
    
    @patch('camera_controller.cv2.VideoCapture')
    def test_get_frame_success(self, mock_video_capture):
        """Test successful frame capture."""
        # Setup mock camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, "mock_frame")
        mock_video_capture.return_value = mock_cap
        
        # Initialize camera
        self.camera_controller.initialize_camera()
        
        result = self.camera_controller.get_frame()
        
        self.assertEqual(result, "mock_frame")
        mock_cap.read.assert_called_once()
    
    @patch('camera_controller.cv2.VideoCapture')
    def test_get_frame_failure(self, mock_video_capture):
        """Test failed frame capture."""
        # Setup mock camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)
        mock_video_capture.return_value = mock_cap
        
        # Initialize camera
        self.camera_controller.initialize_camera()
        
        result = self.camera_controller.get_frame()
        
        self.assertIsNone(result)
    
    @patch('camera_controller.os.makedirs')
    @patch('camera_controller.cv2.imwrite')
    @patch.object(CameraController, 'get_frame')
    def test_take_photo_success(self, mock_get_frame, mock_imwrite, mock_makedirs):
        """Test successful photo capture."""
        # Setup mocks
        mock_frame = "mock_frame_data"
        mock_get_frame.return_value = mock_frame
        mock_imwrite.return_value = True
        
        result = self.camera_controller.take_photo("test_photo.jpg", "test_dir")
        
        self.assertTrue(result)
        mock_makedirs.assert_called_once_with("test_dir", exist_ok=True)
        mock_get_frame.assert_called_once()
        mock_imwrite.assert_called_once()
    
    @patch.object(CameraController, 'get_frame')
    def test_take_photo_no_frame(self, mock_get_frame):
        """Test photo capture when no frame available."""
        mock_get_frame.return_value = None
        
        result = self.camera_controller.take_photo("test_photo.jpg", "test_dir")
        
        self.assertFalse(result)
    
    @patch('camera_controller.os.makedirs')
    @patch('camera_controller.cv2.imwrite')
    @patch.object(CameraController, 'get_frame')
    def test_take_photo_write_failure(self, mock_get_frame, mock_imwrite, mock_makedirs):
        """Test photo capture with write failure."""
        # Setup mocks
        mock_frame = "mock_frame_data"
        mock_get_frame.return_value = mock_frame
        mock_imwrite.side_effect = Exception("Write error")
        
        result = self.camera_controller.take_photo("test_photo.jpg", "test_dir")
        
        self.assertFalse(result)
    
    def test_list_available_cameras(self):
        """Test listing available cameras."""
        with patch('camera_controller.cv2.VideoCapture') as mock_video_capture:
            # Mock 3 available cameras (indices 0, 1, 2)
            def mock_camera_side_effect(index):
                mock_cap = Mock()
                mock_cap.isOpened.return_value = index < 3  # Only first 3 are available
                return mock_cap
            
            mock_video_capture.side_effect = mock_camera_side_effect
            
            result = self.camera_controller.list_available_cameras()
            
            expected_cameras = [0, 1, 2]
            self.assertEqual(result, expected_cameras)
            # Should have tried 10 cameras
            self.assertEqual(mock_video_capture.call_count, 10)
    
    @patch('camera_controller.cv2.VideoCapture')
    def test_get_camera_properties(self, mock_video_capture):
        """Test getting camera properties."""
        # Setup mock camera with properties
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            'frame_width': 1280,
            'frame_height': 720,
            'fps': 30,
            'brightness': 0.5,
            'contrast': 0.5,
            'saturation': 0.5
        }.get(prop, 0)
        mock_video_capture.return_value = mock_cap
        
        # Initialize camera
        self.camera_controller.initialize_camera()
        
        result = self.camera_controller.get_camera_properties()
        
        self.assertIsInstance(result, dict)
        self.assertIn('width', result)
        self.assertIn('height', result)
        self.assertIn('fps', result)
    
    def test_get_camera_properties_no_camera(self):
        """Test getting properties when camera not initialized."""
        result = self.camera_controller.get_camera_properties()
        
        self.assertEqual(result, {})
    
    @patch('camera_controller.cv2.VideoCapture')
    def test_set_camera_property(self, mock_video_capture):
        """Test setting camera property."""
        # Setup mock camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.set.return_value = True
        mock_video_capture.return_value = mock_cap
        
        # Initialize camera
        self.camera_controller.initialize_camera()
        
        result = self.camera_controller.set_camera_property(10, 0.5)  # 10 = CV_CAP_PROP_BRIGHTNESS
        
        self.assertTrue(result)
        mock_cap.set.assert_called_with(10, 0.5)
    
    def test_set_camera_property_no_camera(self):
        """Test setting property when camera not initialized."""
        result = self.camera_controller.set_camera_property(10, 0.5)
        
        self.assertFalse(result)
    
    def test_context_manager(self):
        """Test using CameraController as context manager."""
        with patch('camera_controller.cv2.VideoCapture') as mock_video_capture:
            mock_cap = Mock()
            mock_cap.isOpened.return_value = True
            mock_video_capture.return_value = mock_cap
            
            with CameraController() as camera:
                self.assertIsNotNone(camera)
                # Camera should be initialized
                mock_video_capture.assert_called_once()
            
            # Camera should be released after context
            mock_cap.release.assert_called_once()
    
    @patch('camera_controller.cv2.destroyAllWindows')
    @patch('camera_controller.cv2.VideoCapture')
    def test_release(self, mock_video_capture, mock_destroy_windows):
        """Test camera resource release."""
        # Setup mock camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_video_capture.return_value = mock_cap
        
        # Initialize camera
        self.camera_controller.initialize_camera()
        
        # Release camera
        self.camera_controller.release()
        
        mock_cap.release.assert_called_once()
        mock_destroy_windows.assert_called_once()
        self.assertIsNone(self.camera_controller.cap)


class TestRecordingFunctionality(unittest.TestCase):
    """Test cases for video recording functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.camera_controller = CameraController()
    
    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self.camera_controller, 'cap') and self.camera_controller.cap:
            self.camera_controller.release()
    
    @patch('camera_controller.os.makedirs')
    @patch('camera_controller.cv2.VideoWriter')
    @patch('camera_controller.cv2.VideoCapture')
    def test_start_recording_success(self, mock_video_capture, mock_video_writer_class, mock_makedirs):
        """Test successful recording start."""
        # Setup mocks
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: 30 if prop == 'fps' else 640 if prop == 'width' else 480
        mock_video_capture.return_value = mock_cap
        
        mock_writer = Mock()
        mock_writer.isOpened.return_value = True
        mock_video_writer_class.return_value = mock_writer
        
        # Initialize camera first
        self.camera_controller.initialize_camera()
        
        result = self.camera_controller.start_recording("test.mp4", "test_dir")
        
        self.assertTrue(result)
        self.assertTrue(self.camera_controller.is_recording)
        mock_makedirs.assert_called_once_with("test_dir", exist_ok=True)
    
    def test_start_recording_already_recording(self):
        """Test starting recording when already recording."""
        self.camera_controller.is_recording = True
        
        result = self.camera_controller.start_recording("test.mp4", "test_dir")
        
        self.assertFalse(result)
    
    def test_stop_recording_not_recording(self):
        """Test stopping recording when not recording."""
        result = self.camera_controller.stop_recording()
        
        self.assertFalse(result)
    
    @patch('camera_controller.cv2.VideoWriter')
    def test_stop_recording_success(self, mock_video_writer_class):
        """Test successful recording stop."""
        # Setup recording state
        mock_writer = Mock()
        mock_video_writer_class.return_value = mock_writer
        
        self.camera_controller.is_recording = True
        self.camera_controller.video_writer = mock_writer
        self.camera_controller.recording_filename = "test.mp4"
        
        result = self.camera_controller.stop_recording()
        
        self.assertTrue(result)
        self.assertFalse(self.camera_controller.is_recording)
        mock_writer.release.assert_called_once()
    
    @patch.object(CameraController, 'get_frame')
    def test_record_frame_success(self, mock_get_frame):
        """Test successful frame recording."""
        # Setup mocks
        mock_frame = "mock_frame"
        mock_get_frame.return_value = mock_frame
        
        mock_writer = Mock()
        self.camera_controller.is_recording = True
        self.camera_controller.video_writer = mock_writer
        
        result = self.camera_controller.record_frame()
        
        self.assertTrue(result)
        mock_writer.write.assert_called_once_with(mock_frame)
    
    def test_record_frame_not_recording(self):
        """Test recording frame when not recording."""
        result = self.camera_controller.record_frame()
        
        self.assertFalse(result)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
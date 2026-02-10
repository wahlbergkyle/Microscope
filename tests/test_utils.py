#!/usr/bin/env python3
"""
Test suite for Utility Functions

This module contains unit tests for the utility functions in utils.py.
Run with: python -m pytest tests/test_utils.py
"""

import unittest
from unittest.mock import Mock, patch, mock_open, MagicMock
import sys
import os
import json
import tempfile
import shutil

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    ensure_directory_exists, get_timestamp_filename, validate_file_extension,
    save_config, load_config, get_default_config, format_file_size,
    get_file_info, cleanup_old_files
)


class TestDirectoryOperations(unittest.TestCase):
    """Test cases for directory operations."""
    
    @patch('utils.os.makedirs')
    def test_ensure_directory_exists_success(self, mock_makedirs):
        """Test successful directory creation."""
        result = ensure_directory_exists("/test/path")
        
        self.assertTrue(result)
        mock_makedirs.assert_called_once_with("/test/path", exist_ok=True)
    
    @patch('utils.os.makedirs')
    def test_ensure_directory_exists_failure(self, mock_makedirs):
        """Test directory creation failure."""
        mock_makedirs.side_effect = Exception("Permission denied")
        
        result = ensure_directory_exists("/test/path")
        
        self.assertFalse(result)


class TestFilenameOperations(unittest.TestCase):
    """Test cases for filename operations."""
    
    @patch('utils.datetime')
    def test_get_timestamp_filename(self, mock_datetime):
        """Test timestamp filename generation."""
        # Mock datetime
        mock_now = Mock()
        mock_now.strftime.return_value = "20241024_143022"
        mock_datetime.now.return_value = mock_now
        
        result = get_timestamp_filename("photo", "jpg")
        
        expected = "photo_20241024_143022.jpg"
        self.assertEqual(result, expected)
        mock_now.strftime.assert_called_once_with("%Y%m%d_%H%M%S")
    
    def test_validate_file_extension_valid(self):
        """Test file extension validation with valid extension."""
        result = validate_file_extension("photo.jpg", ["jpg", "png", "bmp"])
        
        self.assertTrue(result)
    
    def test_validate_file_extension_invalid(self):
        """Test file extension validation with invalid extension."""
        result = validate_file_extension("document.pdf", ["jpg", "png", "bmp"])
        
        self.assertFalse(result)
    
    def test_validate_file_extension_case_insensitive(self):
        """Test file extension validation is case insensitive."""
        result = validate_file_extension("PHOTO.JPG", ["jpg", "png"])
        
        self.assertTrue(result)
    
    def test_validate_file_extension_empty_filename(self):
        """Test file extension validation with empty filename."""
        result = validate_file_extension("", ["jpg", "png"])
        
        self.assertFalse(result)
    
    def test_validate_file_extension_no_extension(self):
        """Test file extension validation with no extension."""
        result = validate_file_extension("filename", ["jpg", "png"])
        
        self.assertFalse(result)


class TestConfigOperations(unittest.TestCase):
    """Test cases for configuration operations."""
    
    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config()
        
        self.assertIsInstance(config, dict)
        self.assertIn("camera_index", config)
        self.assertIn("photo_directory", config)
        self.assertIn("video_directory", config)
        self.assertEqual(config["camera_index"], 0)
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('utils.json.dump')
    def test_save_config_success(self, mock_json_dump, mock_file):
        """Test successful configuration saving."""
        test_config = {"camera_index": 1, "photo_directory": "photos"}
        
        result = save_config(test_config, "test_config.json")
        
        self.assertTrue(result)
        mock_file.assert_called_once_with("test_config.json", 'w')
        mock_json_dump.assert_called_once_with(test_config, mock_file.return_value.__enter__.return_value, indent=4)
    
    @patch('builtins.open', side_effect=Exception("File error"))
    def test_save_config_failure(self, mock_file):
        """Test configuration saving failure."""
        test_config = {"camera_index": 1}
        
        result = save_config(test_config, "test_config.json")
        
        self.assertFalse(result)
    
    @patch('utils.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"camera_index": 1}')
    @patch('utils.json.load')
    def test_load_config_success(self, mock_json_load, mock_file, mock_exists):
        """Test successful configuration loading."""
        mock_exists.return_value = True
        expected_config = {"camera_index": 1}
        mock_json_load.return_value = expected_config
        
        result = load_config("test_config.json")
        
        self.assertEqual(result, expected_config)
        mock_exists.assert_called_once_with("test_config.json")
        mock_file.assert_called_once_with("test_config.json", 'r')
    
    @patch('utils.os.path.exists')
    def test_load_config_file_not_exists(self, mock_exists):
        """Test loading configuration when file doesn't exist."""
        mock_exists.return_value = False
        
        result = load_config("nonexistent.json")
        
        self.assertEqual(result, {})
    
    @patch('utils.os.path.exists')
    @patch('builtins.open', side_effect=Exception("Read error"))
    def test_load_config_read_error(self, mock_file, mock_exists):
        """Test loading configuration with read error."""
        mock_exists.return_value = True
        
        result = load_config("test_config.json")
        
        self.assertEqual(result, {})


class TestFileOperations(unittest.TestCase):
    """Test cases for file operations."""
    
    def test_format_file_size_bytes(self):
        """Test file size formatting for bytes."""
        result = format_file_size(1024)
        
        self.assertEqual(result, "1.0 KB")
    
    def test_format_file_size_zero(self):
        """Test file size formatting for zero bytes."""
        result = format_file_size(0)
        
        self.assertEqual(result, "0 B")
    
    def test_format_file_size_large(self):
        """Test file size formatting for large files."""
        # 5.5 MB
        result = format_file_size(5767168)  # 5.5 * 1024 * 1024
        
        self.assertEqual(result, "5.5 MB")
    
    @patch('utils.os.stat')
    @patch('utils.datetime')
    def test_get_file_info_success(self, mock_datetime, mock_stat):
        """Test successful file info retrieval."""
        # Mock file stats
        mock_stat_result = Mock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1634567890
        mock_stat_result.st_ctime = 1634567800
        mock_stat.return_value = mock_stat_result
        
        # Mock datetime
        mock_datetime.fromtimestamp.return_value = "2024-10-24 14:30:22"
        
        result = get_file_info("/test/file.jpg")
        
        self.assertTrue(result["exists"])
        self.assertEqual(result["size"], 1024)
        self.assertEqual(result["size_formatted"], "1.0 KB")
        self.assertEqual(result["extension"], ".jpg")
    
    @patch('utils.os.stat', side_effect=FileNotFoundError())
    def test_get_file_info_not_found(self, mock_stat):
        """Test file info for non-existent file."""
        result = get_file_info("/nonexistent/file.jpg")
        
        self.assertFalse(result["exists"])
    
    def test_cleanup_old_files_no_directory(self):
        """Test cleanup when directory doesn't exist."""
        with patch('utils.os.path.exists', return_value=False):
            result = cleanup_old_files("/nonexistent/dir")
            
            self.assertEqual(result, 0)
    
    @patch('utils.glob.glob')
    @patch('utils.os.path.exists')
    @patch('utils.os.path.isfile')
    @patch('utils.os.path.getmtime')
    @patch('utils.os.remove')
    @patch('utils.time.time')
    def test_cleanup_old_files_success(self, mock_time, mock_remove, mock_getmtime, 
                                      mock_isfile, mock_exists, mock_glob):
        """Test successful cleanup of old files."""
        # Setup mocks
        mock_exists.return_value = True
        mock_time.return_value = 1000000  # Current time
        mock_glob.return_value = ["/test/old_file1.jpg", "/test/old_file2.jpg"]
        mock_isfile.return_value = True
        mock_getmtime.side_effect = [999000, 990000]  # Old files (1000, 10000 seconds old)
        
        result = cleanup_old_files("/test", max_age_days=1)  # 1 day = 86400 seconds
        
        self.assertEqual(result, 2)  # Both files should be deleted
        self.assertEqual(mock_remove.call_count, 2)


class TestTkinterOperations(unittest.TestCase):
    """Test cases for Tkinter-related operations."""
    
    @patch('utils.messagebox.showinfo')
    @patch('utils.tk.Tk')
    def test_show_info_message(self, mock_tk, mock_showinfo):
        """Test showing info message."""
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        # Import and test the function that requires tkinter
        from utils import show_info_message
        show_info_message("Test Title", "Test Message")
        
        mock_tk.assert_called_once()
        mock_root.withdraw.assert_called_once()
        mock_showinfo.assert_called_once_with("Test Title", "Test Message")
        mock_root.destroy.assert_called_once()
    
    @patch('utils.messagebox.showerror')
    @patch('utils.tk.Tk')
    def test_show_error_message(self, mock_tk, mock_showerror):
        """Test showing error message."""
        mock_root = Mock()
        mock_tk.return_value = mock_root
        
        from utils import show_error_message
        show_error_message("Error Title", "Error Message")
        
        mock_tk.assert_called_once()
        mock_root.withdraw.assert_called_once()
        mock_showerror.assert_called_once_with("Error Title", "Error Message")
        mock_root.destroy.assert_called_once()
    
    @patch('utils.messagebox.askyesno')
    @patch('utils.tk.Tk')
    def test_ask_yes_no_true(self, mock_tk, mock_askyesno):
        """Test yes/no dialog returning True."""
        mock_root = Mock()
        mock_tk.return_value = mock_root
        mock_askyesno.return_value = True
        
        from utils import ask_yes_no
        result = ask_yes_no("Question", "Are you sure?")
        
        self.assertTrue(result)
        mock_askyesno.assert_called_once_with("Question", "Are you sure?")
    
    @patch('utils.messagebox.askyesno')
    @patch('utils.tk.Tk')
    def test_ask_yes_no_false(self, mock_tk, mock_askyesno):
        """Test yes/no dialog returning False."""
        mock_root = Mock()
        mock_tk.return_value = mock_root
        mock_askyesno.return_value = False
        
        from utils import ask_yes_no
        result = ask_yes_no("Question", "Are you sure?")
        
        self.assertFalse(result)


class TestIntegrationWithTempFiles(unittest.TestCase):
    """Integration tests using temporary files."""
    
    def setUp(self):
        """Set up temporary directory for tests."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_config_integration(self):
        """Test saving and loading configuration with real files."""
        config_file = os.path.join(self.temp_dir, "test_config.json")
        test_config = {
            "camera_index": 2,
            "photo_directory": "test_photos",
            "video_directory": "test_videos"
        }
        
        # Save config
        save_result = save_config(test_config, config_file)
        self.assertTrue(save_result)
        
        # Load config
        loaded_config = load_config(config_file)
        self.assertEqual(loaded_config, test_config)
    
    def test_file_operations_integration(self):
        """Test file operations with real temporary files."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        
        # Get file info
        file_info = get_file_info(test_file)
        
        self.assertTrue(file_info["exists"])
        self.assertGreater(file_info["size"], 0)
        self.assertEqual(file_info["extension"], ".txt")
        self.assertIn("formatted", file_info["size_formatted"])


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
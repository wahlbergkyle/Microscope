"""
Utility Functions Module

This module contains utility functions for the webcam application
including file operations, image processing helpers, and configuration management.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import tkinter as tk
from tkinter import filedialog, messagebox


def ensure_directory_exists(directory_path: str) -> bool:
    """
    Ensure that a directory exists, create it if it doesn't.
    
    Args:
        directory_path (str): Path to the directory
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False


def get_timestamp_filename(prefix: str = "capture", extension: str = "jpg") -> str:
    """
    Generate a filename with timestamp.
    
    Args:
        prefix (str): Prefix for the filename
        extension (str): File extension without dot
        
    Returns:
        str: Formatted filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """
    Validate if a filename has an allowed extension.
    
    Args:
        filename (str): The filename to validate
        allowed_extensions (List[str]): List of allowed extensions (without dots)
        
    Returns:
        bool: True if extension is allowed, False otherwise
    """
    if not filename:
        return False
    
    file_extension = filename.split('.')[-1].lower()
    return file_extension in [ext.lower() for ext in allowed_extensions]


def save_config(config_data: Dict, config_file: str = "config.json") -> bool:
    """
    Save configuration data to a JSON file.
    
    Args:
        config_data (Dict): Configuration dictionary
        config_file (str): Path to configuration file
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False


def load_config(config_file: str = "config.json") -> Dict:
    """
    Load configuration data from a JSON file.
    
    Args:
        config_file (str): Path to configuration file
        
    Returns:
        Dict: Configuration dictionary or empty dict if failed
    """
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
    
    return {}


def get_default_config() -> Dict:
    """
    Get default configuration settings.
    
    Returns:
        Dict: Default configuration dictionary
    """
    return {
        "camera_index": 0,
        "photo_directory": "photos",
        "video_directory": "videos",
        "photo_format": "jpg",
        "video_format": "mp4",
        "camera_width": 1280,
        "camera_height": 720,
        "camera_fps": 30,
        "auto_timestamp": True,
        "show_preview": True
    }


def choose_save_directory(initial_dir: str = None) -> Optional[str]:
    """
    Open a directory selection dialog.
    
    Args:
        initial_dir (str, optional): Initial directory to open
        
    Returns:
        str or None: Selected directory path or None if cancelled
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    directory = filedialog.askdirectory(
        title="Select Save Directory",
        initialdir=initial_dir or os.getcwd()
    )
    
    root.destroy()
    
    return directory if directory else None


def choose_save_file(filetypes: List[Tuple[str, str]], 
                    initial_dir: str = None,
                    default_extension: str = ".jpg") -> Optional[str]:
    """
    Open a file save dialog.
    
    Args:
        filetypes (List[Tuple[str, str]]): List of (description, pattern) tuples
        initial_dir (str, optional): Initial directory to open
        default_extension (str): Default file extension
        
    Returns:
        str or None: Selected file path or None if cancelled
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    filename = filedialog.asksaveasfilename(
        title="Save File",
        filetypes=filetypes,
        defaultextension=default_extension,
        initialdir=initial_dir or os.getcwd()
    )
    
    root.destroy()
    
    return filename if filename else None


def show_info_message(title: str, message: str):
    """
    Show an information message dialog.
    
    Args:
        title (str): Dialog title
        message (str): Message to display
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    messagebox.showinfo(title, message)
    
    root.destroy()


def show_error_message(title: str, message: str):
    """
    Show an error message dialog.
    
    Args:
        title (str): Dialog title
        message (str): Error message to display
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    messagebox.showerror(title, message)
    
    root.destroy()


def ask_yes_no(title: str, message: str) -> bool:
    """
    Show a yes/no question dialog.
    
    Args:
        title (str): Dialog title
        message (str): Question to ask
        
    Returns:
        bool: True if user clicked Yes, False if No
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    result = messagebox.askyesno(title, message)
    
    root.destroy()
    
    return result


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_file_info(filepath: str) -> Dict:
    """
    Get information about a file.
    
    Args:
        filepath (str): Path to the file
        
    Returns:
        Dict: File information dictionary
    """
    try:
        stat = os.stat(filepath)
        return {
            "exists": True,
            "size": stat.st_size,
            "size_formatted": format_file_size(stat.st_size),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "created": datetime.fromtimestamp(stat.st_ctime),
            "extension": os.path.splitext(filepath)[1].lower()
        }
    except (OSError, FileNotFoundError):
        return {"exists": False}


def cleanup_old_files(directory: str, max_age_days: int = 30, 
                     file_pattern: str = "*") -> int:
    """
    Clean up old files in a directory.
    
    Args:
        directory (str): Directory to clean
        max_age_days (int): Maximum age in days
        file_pattern (str): File pattern to match
        
    Returns:
        int: Number of files deleted
    """
    if not os.path.exists(directory):
        return 0
    
    import glob
    import time
    
    deleted_count = 0
    current_time = time.time()
    max_age_seconds = max_age_days * 24 * 60 * 60
    
    pattern_path = os.path.join(directory, file_pattern)
    
    try:
        for filepath in glob.glob(pattern_path):
            if os.path.isfile(filepath):
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > max_age_seconds:
                    os.remove(filepath)
                    deleted_count += 1
                    print(f"Deleted old file: {filepath}")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    
    return deleted_count
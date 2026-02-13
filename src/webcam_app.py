#!/usr/bin/env python3
"""
USB Webcam Application - GUI Interface

A user-friendly GUI application for controlling USB webcams with features including:
- Live camera preview
- Photo capture
- Video recording
- Multiple camera support
- Settings configuration

Author: Webcam App
Date: 2024
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
import threading
import sys

from PIL import Image
try:
    from PIL import ImageTk
except Exception:
    ImageTk = None
import time
from datetime import datetime
import os

from camera_controller import CameraController
from utils import (
    ensure_directory_exists, get_timestamp_filename, save_config, 
    load_config, get_default_config, show_error_message, show_info_message
)


class WebcamApp:
    """Main GUI application for webcam control."""
    
    def __init__(self, root):
        """
        Initialize the webcam application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("USB Webcam Application")
        self.root.geometry("1600x850")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Initialize variables
        self.camera_controller = None
        self.current_frame = None
        self.preview_running = False
        self.pause_preview_for_recording = False  # Pause preview when recording
        self.recording_thread = None
        self.timelapse_thread = None
        self.timelapse_running = False
        self.config = self.load_application_config()
        self.image_tk_available = False
        self.image_tk_error = None
        
        # Check ImageTk support for preview rendering
        self.image_tk_available, self.image_tk_error = self.check_imagetk_support()
        print(f"ImageTk available: {self.image_tk_available}")

        # Create GUI elements
        print("Setting up GUI...")
        self.setup_gui()
        print("GUI setup complete")
        
        # Initialize camera
        print("Initializing camera...")
        self.initialize_camera()
        print("Camera initialization complete")
        
        # Force canvas update after window is ready
        self.root.after(100, self.force_canvas_update)
        print("WebcamApp initialization complete")
        
    def load_application_config(self):
        """Load application configuration."""
        config = load_config()
        if not config:
            config = get_default_config()
            save_config(config)
        return config
    
    def setup_gui(self):
        """Set up the GUI components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="USB Webcam Application", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status bar - create first so status_var is available
        self.create_status_bar(main_frame)
        
        # Left panel - Controls
        self.create_control_panel(main_frame)
        
        # Center panel - Camera preview
        self.create_preview_panel(main_frame)
        
        # Right panel - Information
        self.create_info_panel(main_frame)
    
    def create_control_panel(self, parent):
        """Create the control panel with buttons and settings."""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), 
                          padx=(0, 10))
        
        # Camera selection
        ttk.Label(control_frame, text="Camera:").grid(row=0, column=0, sticky=tk.W)
        self.camera_var = tk.StringVar(value="Camera 0")
        self.camera_combo = ttk.Combobox(control_frame, textvariable=self.camera_var,
                                        state="readonly", width=25)
        self.camera_combo.grid(row=0, column=1, columnspan=2, pady=5, sticky=(tk.W, tk.E))
        self.camera_combo.bind("<<ComboboxSelected>>", self.on_camera_changed)
        
        # Camera control buttons (underneath combobox)
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Refresh cameras button
        ttk.Button(button_frame, text="Refresh Cameras", 
                  command=self.refresh_cameras).grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        
        # Fix camera button (for black screen issues)
        ttk.Button(button_frame, text="Fix Camera Issues", 
                  command=self.fix_camera_issues).grid(row=0, column=1, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Configure button frame columns to expand evenly
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        
        # Separator
        ttk.Separator(control_frame, orient="horizontal").grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Photo controls
        ttk.Label(control_frame, text="Photo Capture", 
                 font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=3, 
                                                 sticky=tk.W, pady=(0, 5))
        
        self.photo_btn = ttk.Button(control_frame, text="Take Photo", 
                                   command=self.take_photo)
        self.photo_btn.grid(row=4, column=0, columnspan=3, pady=5, 
                           sticky=(tk.W, tk.E))
        
        # Video controls
        ttk.Label(control_frame, text="Video Recording", 
                 font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=3, 
                                                 sticky=tk.W, pady=(10, 5))
        
        self.record_btn = ttk.Button(control_frame, text="Start Recording", 
                                    command=self.toggle_recording)
        self.record_btn.grid(row=6, column=0, columnspan=3, pady=5, 
                            sticky=(tk.W, tk.E))
        
        # Recording status
        self.recording_label = ttk.Label(control_frame, text="", 
                                        foreground="red")
        self.recording_label.grid(row=7, column=0, columnspan=3, pady=5)
        
        # Timelapse controls
        ttk.Label(control_frame, text="Timelapse Capture", 
                 font=("Arial", 10, "bold")).grid(row=8, column=0, columnspan=3, 
                                                 sticky=tk.W, pady=(10, 5))
        
        # Timelapse settings frame
        timelapse_frame = ttk.Frame(control_frame)
        timelapse_frame.grid(row=9, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        # Number of photos
        ttk.Label(timelapse_frame, text="Count:").grid(row=0, column=0, sticky=tk.W)
        self.timelapse_count_var = tk.IntVar(value=10)
        count_spinbox = ttk.Spinbox(timelapse_frame, from_=1, to=1000, 
                                   textvariable=self.timelapse_count_var, width=8)
        count_spinbox.grid(row=0, column=1, padx=(5, 0), sticky=tk.W)
        
        # Interval
        ttk.Label(timelapse_frame, text="Interval (s):").grid(row=1, column=0, sticky=tk.W)
        self.timelapse_interval_var = tk.DoubleVar(value=5.0)
        interval_spinbox = ttk.Spinbox(timelapse_frame, from_=0.1, to=3600, increment=0.5,
                                      textvariable=self.timelapse_interval_var, width=8)
        interval_spinbox.grid(row=1, column=1, padx=(5, 0), sticky=tk.W)
        
        # Timelapse button
        self.timelapse_btn = ttk.Button(control_frame, text="Start Timelapse", 
                                       command=self.start_timelapse)
        self.timelapse_btn.grid(row=10, column=0, columnspan=3, pady=5, 
                               sticky=(tk.W, tk.E))
        
        # Timelapse status
        self.timelapse_label = ttk.Label(control_frame, text="", 
                                        foreground="blue")
        self.timelapse_label.grid(row=11, column=0, columnspan=3, pady=2)
        
        # Separator
        ttk.Separator(control_frame, orient="horizontal").grid(
            row=12, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Camera Settings
        ttk.Label(control_frame, text="Camera Settings", 
                 font=("Arial", 10, "bold")).grid(row=13, column=0, columnspan=3, 
                                                 sticky=tk.W, pady=(0, 5))
        
        # Auto Exposure Toggle
        self.auto_exposure_var = tk.BooleanVar(value=True)
        auto_exposure_cb = ttk.Checkbutton(control_frame, text="Auto Exposure", 
                                          variable=self.auto_exposure_var,
                                          command=self.on_auto_exposure_changed)
        auto_exposure_cb.grid(row=14, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        # Exposure Control
        ttk.Label(control_frame, text="Exposure:").grid(row=15, column=0, sticky=tk.W)
        self.exposure_var = tk.DoubleVar(value=300.0)
        self.exposure_scale = ttk.Scale(control_frame, from_=10.0, to=625.0, 
                                       variable=self.exposure_var, orient=tk.HORIZONTAL,
                                       command=self.on_exposure_changed)
        self.exposure_scale.grid(row=15, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Exposure Entry Field
        self.exposure_entry = ttk.Entry(control_frame, width=8)
        self.exposure_entry.insert(0, "300.0")
        self.exposure_entry.grid(row=15, column=2, sticky=tk.W, padx=(5, 0))
        self.exposure_entry.bind('<Return>', self.on_exposure_entry)
        self.exposure_entry.bind('<FocusOut>', self.on_exposure_entry)
        self.exposure_entry.bind('<Tab>', lambda e: self.on_exposure_entry(e) or 'break')
        
        # Gain Control
        ttk.Label(control_frame, text="Gain:").grid(row=16, column=0, sticky=tk.W)
        self.gain_var = tk.DoubleVar(value=0.0)
        self.gain_scale = ttk.Scale(control_frame, from_=0.0, to=100.0, 
                                   variable=self.gain_var, orient=tk.HORIZONTAL,
                                   command=self.on_gain_changed)
        self.gain_scale.grid(row=16, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Gain Entry Field
        self.gain_entry = ttk.Entry(control_frame, width=8)
        self.gain_entry.insert(0, "0.0")
        self.gain_entry.grid(row=16, column=2, sticky=tk.W, padx=(5, 0))
        self.gain_entry.bind('<Return>', self.on_gain_entry)
        self.gain_entry.bind('<FocusOut>', self.on_gain_entry)
        self.gain_entry.bind('<Tab>', lambda e: self.on_gain_entry(e) or 'break')
        
        # Separator
        ttk.Separator(control_frame, orient="horizontal").grid(
            row=17, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Directory Settings
        ttk.Label(control_frame, text="Directories", 
                 font=("Arial", 10, "bold")).grid(row=18, column=0, columnspan=3, 
                                                 sticky=tk.W, pady=(0, 5))
        
        ttk.Button(control_frame, text="Photo Directory", 
                  command=self.select_photo_directory).grid(row=19, column=0, 
                                                           columnspan=3, pady=2, 
                                                           sticky=(tk.W, tk.E))
        
        ttk.Button(control_frame, text="Video Directory", 
                  command=self.select_video_directory).grid(row=20, column=0, 
                                                           columnspan=3, pady=2, 
                                                           sticky=(tk.W, tk.E))
        
        # Configure column weights
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)
    
    def create_preview_panel(self, parent):
        """Create the camera preview panel."""
        preview_frame = ttk.LabelFrame(parent, text="Camera Preview", padding="10")
        preview_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Preview canvas
        self.preview_canvas = tk.Canvas(preview_frame, width=640, height=480, 
                                       bg="black")
        self.preview_canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clicking canvas should unfocus entry fields
        self.preview_canvas.bind('<Button-1>', lambda e: self.preview_canvas.focus_set())
        
        # Preview controls
        controls_frame = ttk.Frame(preview_frame)
        controls_frame.grid(row=1, column=0, pady=(10, 0), sticky=(tk.W, tk.E))
        
        self.preview_btn = ttk.Button(controls_frame, text="Start Preview", 
                                     command=self.toggle_preview)
        self.preview_btn.pack(side=tk.LEFT)
        
        # Preview info
        self.preview_info = ttk.Label(controls_frame, text="Preview stopped")
        self.preview_info.pack(side=tk.RIGHT)

        if not self.image_tk_available:
            self.preview_btn.config(state=tk.DISABLED)
            reason = self.image_tk_error or "ImageTk not available"
            self.preview_info.config(text="Preview disabled")
            self.status_var.set(f"Preview disabled: {reason}")
        
        # Configure weights
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        controls_frame.columnconfigure(0, weight=1)
    
    def create_info_panel(self, parent):
        """Create the collapsible information panel."""
        # Main container for info panel
        self.info_container = ttk.Frame(parent)
        self.info_container.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), 
                                padx=(10, 0))
        
        # Header with toggle button
        header_frame = ttk.Frame(self.info_container)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Toggle button for collapsing/expanding (start collapsed)
        self.info_collapsed = tk.BooleanVar(value=True)
        self.info_toggle_btn = ttk.Button(header_frame, text="▶ Information", 
                                         command=self.toggle_info_panel)
        self.info_toggle_btn.grid(row=0, column=0, sticky=tk.W)
        
        # Collapsible content frame
        self.info_content_frame = ttk.LabelFrame(self.info_container, text="", padding="10")
        self.info_content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Camera info text widget
        self.info_text = tk.Text(self.info_content_frame, width=30, height=15, 
                                wrap=tk.WORD, state=tk.DISABLED)
        info_scrollbar = ttk.Scrollbar(self.info_content_frame, orient="vertical", 
                                      command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)
        
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        info_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure weights
        header_frame.columnconfigure(0, weight=1)
        self.info_container.columnconfigure(0, weight=1)
        self.info_container.rowconfigure(1, weight=1)
        self.info_content_frame.columnconfigure(0, weight=1)
        self.info_content_frame.rowconfigure(0, weight=1)
        
        # Start collapsed (hide content frame)
        self.info_content_frame.grid_remove()
        
        # Update info initially
        self.update_info_panel()
    
    def toggle_info_panel(self):
        """Toggle the visibility of the information panel."""
        if self.info_collapsed.get():
            # Currently collapsed, expand it
            self.info_content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            self.info_toggle_btn.config(text="▼ Information")
            self.info_collapsed.set(False)
        else:
            # Currently expanded, collapse it
            self.info_content_frame.grid_remove()
            self.info_toggle_btn.config(text="▶ Information")
            self.info_collapsed.set(True)
    
    def create_status_bar(self, parent):
        """Create the status bar."""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), 
                         pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT)
        
        # Time label
        self.time_var = tk.StringVar()
        time_label = ttk.Label(status_frame, textvariable=self.time_var)
        time_label.pack(side=tk.RIGHT)
        
        # Update time
        self.update_time()
    
    def initialize_camera(self):
        """Initialize the camera controller with auto-detection."""
        camera_index = self.config.get("camera_index", 0)
        self.camera_controller = CameraController(camera_index)
        
        if self.camera_controller.initialize_camera():
            # Camera was successfully initialized (possibly with auto-detection)
            actual_index = self.camera_controller.camera_index
            if actual_index != camera_index:
                # Camera index was changed by auto-detection
                self.config["camera_index"] = actual_index
                save_config(self.config)
                self.status_var.set(f"Auto-detected and using Camera {actual_index}")
            else:
                self.status_var.set(f"Camera {actual_index} initialized")
            
            # Don't refresh cameras immediately - it creates conflicts on Windows
            # Just populate with current camera
            self.camera_combo['values'] = [f"Camera {actual_index}"]
            self.camera_combo.set(f"Camera {actual_index}")
            
            self.initialize_camera_controls()
        else:
            self.status_var.set("No cameras found")
            show_error_message("Camera Error", 
                             "No working cameras found. Please check that a camera is connected and not in use by another application.")
    
    def initialize_camera_controls(self):
        """Initialize camera control values from current camera settings."""
        if not self.camera_controller:
            return
        
        properties = self.camera_controller.get_camera_properties()
        if not properties:
            return
        
        # Update exposure and gain ranges if needed
        exposure_range = self.camera_controller.get_exposure_range()
        gain_range = self.camera_controller.get_gain_range()
        
        # Store ranges for info panel
        self.current_exposure_range = exposure_range
        self.current_gain_range = gain_range
        
        # Track what ranges were detected
        range_info = []
        
        if exposure_range != (0.0, 0.0):
            self.exposure_scale.config(from_=exposure_range[0], to=exposure_range[1])
            range_info.append(f"Exposure: {exposure_range[0]:.1f}-{exposure_range[1]:.1f}")
        
        if gain_range != (0.0, 0.0):
            self.gain_scale.config(from_=gain_range[0], to=gain_range[1])
            range_info.append(f"Gain: {gain_range[0]:.1f}-{gain_range[1]:.1f}")
        
        # Display detected ranges in status
        if range_info:
            print(f"Camera ranges detected: {', '.join(range_info)}")
        
        # Set current values
        current_exposure = properties.get('exposure', -6.0)
        current_gain = properties.get('gain', 0.0)
        current_auto_exp = properties.get('auto_exposure', 0.75)
        
        # Check if we're in auto exposure mode
        auto_enabled = (current_auto_exp == 3.0 or current_auto_exp == 0.75)
        
        # If not in auto mode, clamp and set values to ensure camera is in correct state
        if not auto_enabled:
            # Clamp values to detected ranges
            if exposure_range != (0.0, 0.0):
                current_exposure = max(exposure_range[0], min(exposure_range[1], current_exposure))
            if gain_range != (0.0, 0.0):
                current_gain = max(gain_range[0], min(gain_range[1], current_gain))
            
            # Actually set the values to the camera to ensure correct state
            self.camera_controller.set_exposure_time(current_exposure)
            self.camera_controller.set_gain(current_gain)
        
        # Update UI controls without triggering callbacks
        self.exposure_var.set(current_exposure)
        self.gain_var.set(current_gain)
        # V4L2: 3=auto, 1=manual; OpenCV: 0.75=auto, 0.25=manual
        self.auto_exposure_var.set(auto_enabled)
        
        # Update entry fields
        self.exposure_entry.delete(0, tk.END)
        self.exposure_entry.insert(0, f"{current_exposure:.1f}")
        self.gain_entry.delete(0, tk.END)
        self.gain_entry.insert(0, f"{current_gain:.1f}")
        
        # Set exposure scale state based on auto exposure
        auto_enabled = (current_auto_exp == 3.0 or current_auto_exp == 0.75)
        state = 'disabled' if auto_enabled else 'normal'
        self.exposure_scale.config(state=state)
    
    def refresh_cameras(self):
        """Refresh the list of available cameras."""
        if self.camera_controller:
            available_cameras = self.camera_controller.list_available_cameras(verbose=False)
            
            if available_cameras:
                # Create detailed camera options with resolution info
                camera_options = []
                for i in available_cameras:
                    info = self.camera_controller.get_camera_info(i)
                    if info['available']:
                        if info['width'] and info['height']:
                            option = f"Camera {i} ({info['width']}x{info['height']})"
                        else:
                            option = f"Camera {i}"
                        camera_options.append(option)
                    else:
                        camera_options.append(f"Camera {i}")
                
                self.camera_combo['values'] = camera_options
                
                # Set current selection to match active camera
                current_index = self.camera_controller.camera_index
                current_option = None
                for option in camera_options:
                    if f"Camera {current_index}" in option:
                        current_option = option
                        break
                
                if current_option:
                    self.camera_var.set(current_option)
                elif camera_options:
                    self.camera_combo.current(0)
            else:
                self.camera_combo['values'] = ["No cameras found"]
                self.camera_var.set("No cameras found")
            
            self.update_info_panel()
    
    def fix_camera_issues(self):
        """Fix camera issues like black screens by reinitializing with different settings."""
        if not self.camera_controller:
            show_error_message("Camera Error", "No camera controller available")
            return
        
        self.status_var.set("Fixing camera issues...")
        
        # Stop preview if running
        was_previewing = self.preview_running
        if self.preview_running:
            self.toggle_preview()
        
        try:
            # Check camera health first
            if not self.camera_controller.check_camera_health():
                self.status_var.set("Camera unhealthy, reinitializing...")
                
                # Try to reinitialize the camera
                if self.camera_controller.reinitialize_camera():
                    self.status_var.set("Camera reinitialized successfully")
                    show_info_message("Camera Fixed", 
                                    "Camera has been reinitialized. The black screen issue should be resolved.")
                else:
                    self.status_var.set("Camera reinitialization failed")
                    show_error_message("Camera Error", 
                                     "Failed to fix camera. Try unplugging and reconnecting the USB cable.")
            else:
                self.status_var.set("Camera appears healthy")
                show_info_message("Camera Status", "Camera appears to be working normally.")
            
            # Update camera info
            self.refresh_cameras()
            
            # Restart preview if it was running
            if was_previewing:
                self.root.after(500, self.toggle_preview)  # Small delay before restarting
                
        except Exception as e:
            self.status_var.set("Error fixing camera")
            show_error_message("Camera Error", f"Error while fixing camera: {e}")
    
    def on_camera_changed(self, event=None):
        """Handle camera selection change."""
        if "Camera" in self.camera_var.get():
            camera_index = int(self.camera_var.get().split()[-1])
            
            # Stop preview if running
            if self.preview_running:
                self.toggle_preview()
            
            # Release current camera and initialize new one
            if self.camera_controller:
                self.camera_controller.release()
            
            self.camera_controller = CameraController(camera_index)
            if self.camera_controller.initialize_camera():
                self.status_var.set(f"Switched to Camera {camera_index}")
                self.config["camera_index"] = camera_index
                save_config(self.config)
                # Update slider ranges for the new camera
                self.initialize_camera_controls()
                self.update_info_panel()
            else:
                self.status_var.set(f"Failed to initialize Camera {camera_index}")
    
    def toggle_preview(self):
        """Toggle camera preview on/off."""
        if not self.camera_controller:
            return

        if not self.image_tk_available:
            show_error_message("Preview Unavailable", 
                             f"Preview requires Pillow ImageTk/Tk support. {self.image_tk_error or ''}")
            return
        
        if self.preview_running:
            self.preview_running = False
            self.preview_btn.config(text="Start Preview")
            self.preview_info.config(text="Preview stopped")
            self.status_var.set("Preview stopped")
        else:
            self.preview_running = True
            self.preview_btn.config(text="Stop Preview")
            self.preview_info.config(text="Preview running")
            self.status_var.set("Preview started")
            threading.Thread(target=self.preview_loop, daemon=True).start()
    
    def preview_loop(self):
        """Main loop for camera preview with black frame detection."""
        # Flush initial frames on Windows DirectShow to avoid black frames
        if sys.platform.startswith('win') and self.camera_controller and self.camera_controller.cap:
            print("Flushing initial frames for warm-up...")
            for _ in range(5):
                try:
                    self.camera_controller.cap.read()
                except:
                    pass
                time.sleep(0.02)
            print("Starting preview loop...")
        
        black_frame_count = 0
        max_black_frames = 30  # Allow some black frames before taking action
        failed_frame_count = 0
        max_failed_frames = 100  # Only reinit after many failures
        frame_count = 0
        
        while self.preview_running:
            try:
                # Pause this loop when recording is active (recording_loop handles preview)
                if self.pause_preview_for_recording:
                    if frame_count < 2:  # Only print once
                        print("Preview loop PAUSED - recording loop has camera ownership")
                    time.sleep(0.1)  # Just wait while recording handles everything
                    continue
                
                frame = self.camera_controller.get_frame()
                frame_count += 1
                
                # Debug output
                if frame is not None:
                    if frame_count <= 5:
                        print(f"Frame {frame_count}: Got frame {frame.shape}, mean={frame.mean():.2f}")
                else:
                    if frame_count <= 10:
                        print(f"Frame {frame_count}: None - check camera connection")
                
                if frame is not None:
                    failed_frame_count = 0  # Reset failed count on success
                    # Check if frame is mostly black
                    frame_mean = frame.mean()
                    if frame_mean <= 1.0:  # Very dark/black frame
                        black_frame_count += 1
                        if black_frame_count >= max_black_frames:
                            print("Too many black frames, attempting camera fix...")
                            self.root.after(0, self.status_var.set, "Black screen detected, fixing camera...")
                            
                            # Try to fix camera in main thread
                            self.root.after(0, self._auto_fix_black_screen)
                            black_frame_count = 0  # Reset counter
                    else:
                        black_frame_count = 0  # Reset on good frame
                    
                    self.current_frame = frame
                    # Schedule GUI update in main thread
                    self.root.after(0, self.update_preview, frame)
                else:
                    # If no frame, count failures before attempting reinit
                    failed_frame_count += 1
                    if failed_frame_count >= max_failed_frames:
                        print(f"Camera failed {max_failed_frames} times, attempting reinit...")
                        if not self.camera_controller.initialize_camera():
                            print("Warning: Camera reinitialization failed")
                        failed_frame_count = 0  # Reset counter
                time.sleep(0.033)  # ~30 FPS
            except Exception as e:
                print(f"Preview loop error: {e}")
                time.sleep(0.1)  # Brief pause on error
    
    def _auto_fix_black_screen(self):
        """Automatically attempt to fix black screen issues."""
        if self.camera_controller and self.camera_controller.reinitialize_camera():
            self.status_var.set("Black screen fixed automatically")
        else:
            self.status_var.set("Auto-fix failed - use Fix Camera button")
    
    def update_preview(self, frame):
        """Update the preview canvas with new frame."""
        if not self.image_tk_available:
            return
        if frame is None:
            print("Warning: Received None frame in update_preview")
            return
        
        # Resize frame to fit canvas
        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()
        
        # Use configured canvas size if actual size not yet available
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 640  # Default canvas width
            canvas_height = 480  # Default canvas height
        
        try:
            # Validate frame before processing
            if frame.size == 0 or len(frame.shape) < 2:
                return
            
            # Ensure frame is contiguous in memory (fixes Windows matrix errors)
            if not frame.flags['C_CONTIGUOUS']:
                frame = np.ascontiguousarray(frame)
            
            # Calculate scaling to maintain aspect ratio
            h, w = frame.shape[:2]
            scale = min(canvas_width / w, canvas_height / h)
            new_width = int(w * scale)
            new_height = int(h * scale)
            
            # Resize frame
            resized_frame = cv2.resize(frame, (new_width, new_height))
            
            # Convert BGR to RGB
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            
            # Ensure RGB frame is also contiguous
            if not rgb_frame.flags['C_CONTIGUOUS']:
                rgb_frame = np.ascontiguousarray(rgb_frame)
            
            # Convert to PIL Image and then to PhotoImage
            pil_image = Image.fromarray(rgb_frame)
            photo = ImageTk.PhotoImage(pil_image)
            
            # Update canvas
            self.preview_canvas.delete("all")
            x = (canvas_width - new_width) // 2
            y = (canvas_height - new_height) // 2
            self.preview_canvas.create_image(x, y, anchor=tk.NW, image=photo)
            
            # Keep a reference to prevent garbage collection
            self.preview_canvas.image = photo
            
        except Exception as e:
            print(f"Error updating preview: {e}")
            print(f"Frame shape: {frame.shape if frame is not None else 'None'}")
            print(f"Canvas size: {canvas_width}x{canvas_height}")
    
    def force_canvas_update(self):
        """Force canvas to update its size information."""
        self.preview_canvas.update_idletasks()

    def check_imagetk_support(self):
        """Check whether Pillow ImageTk is usable with the current Tk environment."""
        if ImageTk is None:
            return False, "Pillow ImageTk is not installed or failed to import"
        try:
            test_image = Image.new("RGB", (1, 1))
            ImageTk.PhotoImage(test_image)
            return True, None
        except Exception as e:
            return False, str(e)
        
    def take_photo(self):
        """Take a photo."""
        if not self.camera_controller:
            show_error_message("Error", "Camera not initialized")
            return
        
        photo_dir = self.config.get("photo_directory", "photos")
        ensure_directory_exists(photo_dir)
        
        filename = get_timestamp_filename("photo", "jpg")
        
        success, frame = self.camera_controller.take_photo(filename, photo_dir)
        if success:
            self.status_var.set(f"Photo saved: {filename}")
            # Display the captured photo in preview
            if frame is not None and self.image_tk_available:
                self.update_preview(frame)
            show_info_message("Success", f"Photo saved as {filename}")
        else:
            self.status_var.set("Failed to take photo")
            show_error_message("Error", "Failed to take photo")
    
    def toggle_recording(self):
        """Toggle video recording on/off."""
        if not self.camera_controller:
            show_error_message("Error", "Camera not initialized")
            return
        
        if not self.camera_controller.is_recording:
            # Start recording
            video_dir = self.config.get("video_directory", "videos")
            ensure_directory_exists(video_dir)
            
            filename = get_timestamp_filename("video", "mp4")  # Use .mp4 for best compatibility
            
            if self.camera_controller.start_recording(filename, video_dir):
                self.record_btn.config(text="Stop Recording")
                self.recording_label.config(text="● REC")
                self.status_var.set("Recording started")
                
                # Pause preview loop to avoid competing for camera frames
                # Recording loop will handle both recording AND preview updates
                self.pause_preview_for_recording = True
                
                # Start recording thread
                self.recording_thread = threading.Thread(target=self.recording_loop, 
                                                        daemon=True)
                self.recording_thread.start()
            else:
                show_error_message("Error", "Failed to start recording")
        else:
            # Stop recording
            if self.camera_controller.stop_recording():
                self.record_btn.config(text="Start Recording")
                self.recording_label.config(text="")
                self.status_var.set("Recording stopped")
                
                # Resume preview loop
                self.pause_preview_for_recording = False
                
                show_info_message("Success", "Recording saved successfully")
            else:
                show_error_message("Error", "Failed to stop recording")
    
    def recording_loop(self):
        """Loop for continuous video recording."""
        frames_recorded = 0
        last_preview_time = time.time()
        preview_interval = 0.05  # Update preview every 50ms for smooth playback
        
        print("Recording loop started - this is now the sole frame source")
        
        while self.camera_controller and self.camera_controller.is_recording:
            # record_frame() is the SOLE source of frames from camera during recording
            # This prevents preview_loop from competing for camera access
            success, frame = self.camera_controller.record_frame()
            if success:
                frames_recorded += 1
                self.current_frame = frame  # Update current frame for other uses
                
                # Update preview periodically to reduce GUI overhead
                # But less frequently than frame capture for maximum recording speed
                current_time = time.time()
                if current_time - last_preview_time >= preview_interval and self.image_tk_available:
                    if frame is not None:
                        # Schedule GUI update in main thread
                        self.root.after(0, self.update_preview, frame)
                    last_preview_time = current_time
            else:
                # Failed to record frame
                if self.camera_controller.is_recording:
                    print(f"Warning: Failed to record frame {frames_recorded + 1}")
                    # Small delay on failure to avoid tight loop
                    time.sleep(0.001)
            
            # No sleep on success - run as fast as camera can provide frames
        
        print(f"Recording loop ended: {frames_recorded} frames recorded by loop")
    
    def start_timelapse(self):
        """Start timelapse capture."""
        if not self.camera_controller:
            show_error_message("Error", "Camera not initialized")
            return
        
        if self.timelapse_running:
            show_error_message("Error", "Timelapse already in progress")
            return
        
        # Get settings
        count = self.timelapse_count_var.get()
        interval = self.timelapse_interval_var.get()
        
        if count < 1:
            show_error_message("Error", "Photo count must be at least 1")
            return
        
        if interval < 0.1:
            show_error_message("Error", "Interval must be at least 0.1 seconds")
            return
        
        # Get camera settings
        exposure = None if self.auto_exposure_var.get() else self.exposure_var.get()
        gain = self.gain_var.get()
        auto_exposure = self.auto_exposure_var.get()
        
        # Start timelapse in separate thread
        self.timelapse_running = True
        self.timelapse_btn.config(text="Stop Timelapse", command=self.stop_timelapse)
        self.timelapse_label.config(text=f"Starting timelapse...")
        
        self.timelapse_thread = threading.Thread(
            target=self.timelapse_worker,
            args=(count, interval, exposure, gain, auto_exposure),
            daemon=True
        )
        self.timelapse_thread.start()
        
        self.status_var.set(f"Timelapse started: {count} photos, {interval}s intervals")
    
    def stop_timelapse(self):
        """Stop timelapse capture."""
        self.timelapse_running = False
        self.timelapse_btn.config(text="Start Timelapse", command=self.start_timelapse)
        self.timelapse_label.config(text="Timelapse stopped")
        self.status_var.set("Timelapse stopped by user")
    
    def timelapse_worker(self, count, interval, exposure, gain, auto_exposure):
        """Worker thread for timelapse capture."""
        try:
            output_dir = self.config.get("photo_directory", "photos")
            
            def progress_callback(current, total, filename):
                """Update GUI from timelapse progress."""
                if self.timelapse_running:
                    remaining = total - current
                    estimated_time = remaining * interval
                    self.timelapse_label.config(
                        text=f"Photo {current}/{total} - Est. {estimated_time:.0f}s remaining"
                    )
                    self.status_var.set(f"Captured: {filename}")
            
            captured_files = self.camera_controller.capture_timelapse_series(
                num_photos=count,
                interval_seconds=interval,
                output_dir=output_dir,
                exposure=exposure,
                gain=gain,
                auto_exposure=auto_exposure,
                progress_callback=progress_callback
            )
            
            # Update GUI on completion
            if self.timelapse_running:  # Only update if not manually stopped
                self.timelapse_running = False
                self.timelapse_btn.config(text="Start Timelapse", command=self.start_timelapse)
                
                if captured_files:
                    self.timelapse_label.config(text=f"Complete: {len(captured_files)} photos captured")
                    self.status_var.set(f"Timelapse complete: {len(captured_files)} photos")
                    show_info_message("Timelapse Complete", 
                                    f"Successfully captured {len(captured_files)} photos\n"
                                    f"Location: {output_dir}")
                else:
                    self.timelapse_label.config(text="Failed: No photos captured")
                    self.status_var.set("Timelapse failed")
                    show_error_message("Timelapse Failed", "No photos were captured")
        
        except Exception as e:
            self.timelapse_running = False
            self.timelapse_btn.config(text="Start Timelapse", command=self.start_timelapse)
            self.timelapse_label.config(text="Error occurred")
            self.status_var.set(f"Timelapse error: {e}")
            show_error_message("Timelapse Error", f"An error occurred: {e}")
    
    def select_photo_directory(self):
        """Select directory for saving photos."""
        directory = filedialog.askdirectory(
            title="Select Photo Directory",
            initialdir=self.config.get("photo_directory", "photos")
        )
        
        if directory:
            self.config["photo_directory"] = directory
            save_config(self.config)
            self.status_var.set(f"Photo directory: {directory}")
            self.update_info_panel()
    
    def select_video_directory(self):
        """Select directory for saving videos."""
        directory = filedialog.askdirectory(
            title="Select Video Directory",
            initialdir=self.config.get("video_directory", "videos")
        )
        
        if directory:
            self.config["video_directory"] = directory
            save_config(self.config)
            self.status_var.set(f"Video directory: {directory}")
            self.update_info_panel()
    
    def on_auto_exposure_changed(self):
        """Handle auto exposure checkbox change."""
        if not self.camera_controller:
            return
        
        auto_enabled = self.auto_exposure_var.get()
        success = self.camera_controller.set_auto_exposure(auto_enabled)
        
        # Enable/disable manual exposure control
        state = 'disabled' if auto_enabled else 'normal'
        self.exposure_scale.config(state=state)
        
        if success:
            if auto_enabled:
                self.status_var.set("Auto exposure enabled")
            else:
                self.status_var.set("Manual exposure enabled")
            
            # On Windows, camera stream may need recovery after mode change
            if sys.platform.startswith('win'):
                # Give camera time to adjust and flush frames
                time.sleep(0.1)
                # Test if camera is still responding
                test_frame = self.camera_controller.get_frame()
                if test_frame is None:
                    print("Warning: Camera stream disrupted after auto exposure change, attempting recovery...")
                    # Try to recover by reinitializing
                    if self.camera_controller.reinitialize_camera():
                        self.status_var.set("Auto exposure changed (camera recovered)")
                    else:
                        self.status_var.set("Camera stream disrupted - use Fix Camera button")
        else:
            self.status_var.set("Failed to change auto exposure setting")
        
        self.update_info_panel()
    
    def on_exposure_changed(self, value):
        """Handle exposure slider change."""
        if not self.camera_controller or self.auto_exposure_var.get():
            return
        
        exposure_value = float(value)
        success = self.camera_controller.set_exposure_time(exposure_value)
        
        # Update entry field
        self.exposure_entry.delete(0, tk.END)
        self.exposure_entry.insert(0, f"{exposure_value:.1f}")
        
        if success:
            self.status_var.set(f"Exposure set to {exposure_value:.1f}")
        else:
            self.status_var.set("Failed to set exposure")
    
    def on_gain_changed(self, value):
        """Handle gain slider change."""
        if not self.camera_controller:
            return
        
        gain_value = float(value)
        
        # Special handling for gain = 0
        if gain_value == 0.0:
            success = self.camera_controller.set_gain(gain_value)
            # Update entry field
            self.gain_entry.delete(0, tk.END)
            self.gain_entry.insert(0, f"{gain_value:.1f}")
            
            if success:
                self.status_var.set("Gain set to 0.0 (minimum gain)")
            else:
                self.status_var.set("Gain set to 0.0")
            return
        
        success = self.camera_controller.set_gain(gain_value)
        
        # Update entry field
        self.gain_entry.delete(0, tk.END)
        self.gain_entry.insert(0, f"{gain_value:.1f}")
        
        if success:
            # Verify the actual value set
            actual_gain = self.camera_controller.cap.get(cv2.CAP_PROP_GAIN) if self.camera_controller.cap else gain_value
            if abs(actual_gain - gain_value) > 1.0:
                self.status_var.set(f"Gain set to {actual_gain:.1f} (camera adjusted from {gain_value:.1f})")
            else:
                self.status_var.set(f"Gain set to {gain_value:.1f}")
        else:
            self.status_var.set("Failed to set gain (camera may not support gain control)")
    
    def on_exposure_entry(self, event=None):
        """Handle exposure entry field change."""
        if not self.camera_controller or self.auto_exposure_var.get():
            return
        
        try:
            exposure_value = float(self.exposure_entry.get())
            
            # Get slider range and clamp value
            min_exp = self.exposure_scale.cget('from')
            max_exp = self.exposure_scale.cget('to')
            exposure_value = max(min_exp, min(max_exp, exposure_value))
            
            # Set the value and apply it
            self.exposure_var.set(exposure_value)
            # Manually trigger the change to ensure status updates
            self.camera_controller.set_exposure_time(exposure_value)
            
            # Update entry field with clamped value
            self.exposure_entry.delete(0, tk.END)
            self.exposure_entry.insert(0, f"{exposure_value:.1f}")
            
            # Update status
            self.status_var.set(f"Exposure set to {exposure_value:.1f}")
        except ValueError:
            # Invalid input, restore current value
            current_value = self.exposure_var.get()
            self.exposure_entry.delete(0, tk.END)
            self.exposure_entry.insert(0, f"{current_value:.1f}")
            self.status_var.set("Invalid exposure value")
    
    def on_gain_entry(self, event=None):
        """Handle gain entry field change."""
        if not self.camera_controller:
            return
        
        try:
            gain_value = float(self.gain_entry.get())
            
            # Get slider range and clamp value
            min_gain = self.gain_scale.cget('from')
            max_gain = self.gain_scale.cget('to')
            gain_value = max(min_gain, min(max_gain, gain_value))
            
            # Set the value and apply it
            self.gain_var.set(gain_value)
            # Manually trigger the change to ensure status updates
            success = self.camera_controller.set_gain(gain_value)
            
            # Update entry field with clamped value
            self.gain_entry.delete(0, tk.END)
            self.gain_entry.insert(0, f"{gain_value:.1f}")
            
            # Update status (same logic as on_gain_changed)
            if gain_value == 0.0:
                if success:
                    self.status_var.set("Gain set to 0.0 (minimum gain)")
                else:
                    self.status_var.set("Gain set to 0.0")
            elif success:
                actual_gain = self.camera_controller.cap.get(cv2.CAP_PROP_GAIN) if self.camera_controller.cap else gain_value
                if abs(actual_gain - gain_value) > 1.0:
                    self.status_var.set(f"Gain set to {actual_gain:.1f} (camera adjusted from {gain_value:.1f})")
                else:
                    self.status_var.set(f"Gain set to {gain_value:.1f}")
            else:
                self.status_var.set("Failed to set gain (camera may not support gain control)")
        except ValueError:
            # Invalid input, restore current value
            current_value = self.gain_var.get()
            self.gain_entry.delete(0, tk.END)
            self.gain_entry.insert(0, f"{current_value:.1f}")
            self.status_var.set("Invalid gain value")

    def update_info_panel(self):
        """Update the information panel."""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        
        info_lines = []
        info_lines.append("=== Camera Information ===\n")
        
        if self.camera_controller:
            properties = self.camera_controller.get_camera_properties()
            if properties:
                info_lines.append(f"Resolution: {properties.get('width', 'N/A')} x {properties.get('height', 'N/A')}\n")
                info_lines.append(f"FPS: {properties.get('fps', 'N/A')}\n")
                info_lines.append(f"Brightness: {properties.get('brightness', 'N/A'):.2f}\n")
                info_lines.append(f"Contrast: {properties.get('contrast', 'N/A'):.2f}\n")
                info_lines.append(f"Saturation: {properties.get('saturation', 'N/A'):.2f}\n")
                info_lines.append(f"\nExposure: {properties.get('exposure', 'N/A'):.2f}\n")
                
                # Show exposure range if available
                if hasattr(self, 'current_exposure_range') and self.current_exposure_range != (0.0, 0.0):
                    exp_min, exp_max = self.current_exposure_range
                    info_lines.append(f"Exposure Range: {exp_min:.1f} to {exp_max:.1f}\n")
                
                info_lines.append(f"\nGain: {properties.get('gain', 'N/A'):.2f}\n")
                
                # Show gain range if available
                if hasattr(self, 'current_gain_range') and self.current_gain_range != (0.0, 0.0):
                    gain_min, gain_max = self.current_gain_range
                    info_lines.append(f"Gain Range: {gain_min:.1f} to {gain_max:.1f}\n")
                
                auto_exp = properties.get('auto_exposure', 'N/A')
                # V4L2: 3=auto, 1=manual; OpenCV: 0.75=auto, 0.25=manual
                if auto_exp == 3.0 or auto_exp == 0.75:
                    auto_exp_text = "Auto"
                elif auto_exp == 1.0 or auto_exp == 0.25:
                    auto_exp_text = "Manual"
                else:
                    auto_exp_text = f"{auto_exp:.2f}"
                info_lines.append(f"\nAuto Exposure: {auto_exp_text}\n")
            else:
                info_lines.append("Camera not available\n")
        else:
            info_lines.append("Camera not initialized\n")
        
        info_lines.append("\n=== Configuration ===\n")
        info_lines.append(f"Photo Directory: {self.config.get('photo_directory', 'photos')}\n")
        info_lines.append(f"Video Directory: {self.config.get('video_directory', 'videos')}\n")
        info_lines.append(f"Current Camera: {self.config.get('camera_index', 0)}\n")
        
        info_lines.append("\n=== Available Cameras ===\n")
        if self.camera_controller:
            cameras = self.camera_controller.list_available_cameras()
            if cameras:
                for cam in cameras:
                    info_lines.append(f"Camera {cam}\n")
            else:
                info_lines.append("No cameras detected\n")
        
        self.info_text.insert(1.0, "".join(info_lines))
        self.info_text.config(state=tk.DISABLED)
    
    def update_time(self):
        """Update the time display."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_var.set(current_time)
        self.root.after(1000, self.update_time)
    
    def on_closing(self):
        """Handle application closing."""
        # Check for active operations
        active_operations = []
        
        if self.camera_controller and self.camera_controller.is_recording:
            active_operations.append("video recording")
        
        if self.timelapse_running:
            active_operations.append("timelapse capture")
        
        if active_operations:
            operations_text = " and ".join(active_operations)
            if messagebox.askyesno("Active Operations", 
                                 f"The following operations are active: {operations_text}.\n"
                                 "Stop all operations and exit?"):
                if self.camera_controller and self.camera_controller.is_recording:
                    self.camera_controller.stop_recording()
                if self.timelapse_running:
                    self.stop_timelapse()
            else:
                return
        
        self.preview_running = False
        
        if self.camera_controller:
            self.camera_controller.release()
        
        self.root.destroy()


def main():
    """Main function to run the application."""
    root = tk.Tk()
    
    # Set window icon (if available)
    try:
        # You can add an icon file here
        # root.iconbitmap("icon.ico")
        pass
    except:
        pass
    
    try:
        app = WebcamApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
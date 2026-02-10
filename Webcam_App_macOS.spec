# -*- mode: python ; coding: utf-8 -*-
# macOS-specific PyInstaller spec file for Webcam App

import sys
import os

block_cipher = None

a = Analysis(
    ['src/webcam_app.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('webcam_app.png', '.'),   # Include PNG icon for macOS
        ('config.json', '.'),      # Include config if it exists
    ],
    hiddenimports=[
        'cv2', 
        'PIL.Image', 
        'PIL.ImageTk', 
        'tkinter', 
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'numpy',
        'threading',
        'datetime',
        'os',
        'sys',
        'time',
        'glob',
        'json'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # Exclude unnecessary packages to reduce size
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Webcam_App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Webcam_App',
)

app = BUNDLE(
    coll,
    name='Webcam_App.app',
    icon='webcam_app.png',  # macOS will convert PNG to ICNS
    bundle_identifier='com.webcamapp.webcamapp',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'Webcam App',
        'CFBundleDisplayName': 'Webcam App',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleIdentifier': 'com.webcamapp.webcamapp',
        'CFBundleExecutable': 'Webcam_App',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'WBCM',
        'NSCameraUsageDescription': 'This app needs access to the camera to capture photos and videos.',
        'NSMicrophoneUsageDescription': 'This app may need access to the microphone for video recording.',
        'LSMinimumSystemVersion': '10.13.0',  # macOS High Sierra minimum
        'NSHighResolutionCapable': True,
        'NSSupportsAutomaticGraphicsSwitching': True,
        'LSApplicationCategoryType': 'public.app-category.photography',
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeExtensions': ['jpg', 'jpeg', 'png', 'bmp'],
                'CFBundleTypeName': 'Image',
                'CFBundleTypeRole': 'Editor',
                'LSTypeIsPackage': False,
            }
        ],
    },
)
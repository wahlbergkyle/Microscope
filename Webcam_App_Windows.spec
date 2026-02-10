# -*- mode: python ; coding: utf-8 -*-
# Windows-specific PyInstaller spec file for Webcam App

import sys
import os

block_cipher = None

a = Analysis(
    ['src/webcam_app.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('webcam_app.ico', '.'),  # Include icon in the bundle
        ('config.json', '.'),     # Include config if it exists
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
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Webcam_App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='webcam_app.ico',  # Windows icon
    version_file=None,  # Could add version info here
    uac_admin=False,    # Don't require admin privileges
)
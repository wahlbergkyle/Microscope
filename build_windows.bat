@echo off
REM Windows batch file to build Webcam App executable
REM Run this on Windows to create Webcam_App.exe

echo Starting Windows build for Webcam App...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Create icons if they don't exist
if not exist "webcam_app.ico" (
    echo Creating application icons...
    python create_icon.py
)

REM Clean previous build
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

REM Build the application
echo Building Windows executable...
pyinstaller --clean Webcam_App_Windows.spec

if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo SUCCESS: Windows executable created!
echo Location: dist\Webcam_App.exe
echo.
echo To install:
echo 1. Copy dist\Webcam_App.exe to desired location
echo 2. Create desktop shortcut if desired
echo 3. No additional dependencies required

pause
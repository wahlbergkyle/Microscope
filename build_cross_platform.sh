#!/bin/bash
# Cross-platform build script for Webcam App
# Run this script on the target platform to build the executable

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect platform
detect_platform() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        PLATFORM="linux"
        SPEC_FILE="Webcam_App.spec"
        OUTPUT_NAME="Webcam_App"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
        SPEC_FILE="Webcam_App_macOS.spec"
        OUTPUT_NAME="Webcam_App.app"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        PLATFORM="windows"
        SPEC_FILE="Webcam_App_Windows.spec"
        OUTPUT_NAME="Webcam_App.exe"
    else
        print_error "Unsupported platform: $OSTYPE"
        exit 1
    fi
    
    print_status "Detected platform: $PLATFORM"
}

# Check if Python is available
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON="python3"
    elif command -v python &> /dev/null; then
        PYTHON="python"
    else
        print_error "Python not found. Please install Python 3.7 or higher."
        exit 1
    fi
    
    print_status "Using Python: $($PYTHON --version)"
}

# Create virtual environment if it doesn't exist
setup_venv() {
    if [ ! -d ".venv" ]; then
        print_status "Creating virtual environment..."
        $PYTHON -m venv .venv
    fi
    
    # Activate virtual environment
    if [[ "$PLATFORM" == "windows" ]]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
    
    print_status "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        print_warning "requirements.txt not found, installing basic dependencies"
        pip install opencv-python pillow numpy pyinstaller
    fi
    
    # Install PyInstaller if not already installed
    pip install pyinstaller
    
    print_success "Dependencies installed"
}

# Create icons if they don't exist
create_icons() {
    if [ ! -f "webcam_app.png" ] || [ ! -f "webcam_app.ico" ]; then
        print_status "Creating application icons..."
        $PYTHON create_icon.py
        print_success "Icons created"
    else
        print_status "Icons already exist"
    fi
}

# Build the application
build_application() {
    print_status "Building application for $PLATFORM..."
    
    # Clean previous build
    if [ -d "build" ]; then
        rm -rf build
    fi
    if [ -d "dist" ]; then
        rm -rf dist
    fi
    
    # Run PyInstaller
    pyinstaller --clean "$SPEC_FILE"
    
    if [ $? -eq 0 ]; then
        print_success "Build completed successfully!"
        print_success "Executable location: dist/$OUTPUT_NAME"
        
        # Show file size
        if [[ "$PLATFORM" == "macos" ]]; then
            SIZE=$(du -sh "dist/$OUTPUT_NAME" | cut -f1)
        else
            SIZE=$(du -sh "dist/$OUTPUT_NAME" | cut -f1)
        fi
        print_status "Application size: $SIZE"
    else
        print_error "Build failed!"
        exit 1
    fi
}

# Create platform-specific installer/package
create_package() {
    case $PLATFORM in
        "linux")
            print_status "Creating Linux desktop integration..."
            # Desktop file is already created
            if [ -f "Webcam_App.desktop" ]; then
                print_success "Desktop file available: Webcam_App.desktop"
            fi
            ;;
        "macos")
            print_status "Creating macOS DMG installer..."
            if command -v create-dmg &> /dev/null; then
                create-dmg \
                    --volname "Webcam App Installer" \
                    --volicon "webcam_app.png" \
                    --window-pos 200 120 \
                    --window-size 800 400 \
                    --icon-size 100 \
                    --icon "Webcam_App.app" 200 190 \
                    --hide-extension "Webcam_App.app" \
                    --app-drop-link 600 185 \
                    "dist/Webcam_App_Installer.dmg" \
                    "dist/"
                print_success "DMG installer created: dist/Webcam_App_Installer.dmg"
            else
                print_warning "create-dmg not installed. Install with: brew install create-dmg"
                print_status "App bundle created: dist/$OUTPUT_NAME"
            fi
            ;;
        "windows")
            print_status "Windows executable created: dist/$OUTPUT_NAME"
            # Could add NSIS installer creation here
            ;;
    esac
}

# Test the built application
test_application() {
    print_status "Testing built application..."
    
    case $PLATFORM in
        "linux")
            timeout 5s "./dist/$OUTPUT_NAME" || true
            ;;
        "macos")
            timeout 5s "dist/$OUTPUT_NAME/Contents/MacOS/Webcam_App" || true
            ;;
        "windows")
            # On Windows, just check if file exists and is executable
            if [ -f "dist/$OUTPUT_NAME" ]; then
                print_success "Windows executable created successfully"
            fi
            ;;
    esac
}

# Main build process
main() {
    print_status "Starting cross-platform build for Webcam App"
    
    detect_platform
    check_python
    setup_venv
    install_dependencies
    create_icons
    build_application
    create_package
    test_application
    
    print_success "Build process completed for $PLATFORM!"
    
    case $PLATFORM in
        "linux")
            echo
            echo "To install:"
            echo "1. Copy dist/Webcam_App to desired location"
            echo "2. Copy Webcam_App.desktop to ~/Desktop/ or ~/.local/share/applications/"
            ;;
        "macos")
            echo
            echo "To install:"
            echo "1. Open dist/Webcam_App_Installer.dmg (if created)"
            echo "2. Or drag dist/Webcam_App.app to /Applications/"
            ;;
        "windows")
            echo
            echo "To install:"
            echo "1. Copy dist/Webcam_App.exe to desired location"
            echo "2. Create desktop shortcut if desired"
            ;;
    esac
}

# Run main function
main "$@"
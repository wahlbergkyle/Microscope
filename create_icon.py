#!/usr/bin/env python3
"""
Create a simple icon for the webcam application.
"""

from PIL import Image, ImageDraw
import os

def create_webcam_icon(size=64):
    """Create a simple webcam icon."""
    # Create a new image with transparent background
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw camera body (rectangle)
    body_margin = size // 8
    body_coords = [body_margin, size//3, size-body_margin, size*2//3]
    draw.rectangle(body_coords, fill=(64, 64, 64, 255), outline=(0, 0, 0, 255), width=2)
    
    # Draw lens (circle)
    lens_center = size // 2
    lens_radius = size // 6
    lens_coords = [lens_center-lens_radius, lens_center-lens_radius, 
                   lens_center+lens_radius, lens_center+lens_radius]
    draw.ellipse(lens_coords, fill=(32, 32, 32, 255), outline=(0, 0, 0, 255), width=2)
    
    # Draw lens center (smaller circle)
    center_radius = size // 12
    center_coords = [lens_center-center_radius, lens_center-center_radius,
                     lens_center+center_radius, lens_center+center_radius]
    draw.ellipse(center_coords, fill=(128, 128, 255, 255))
    
    # Draw mounting (small rectangle at top)
    mount_width = size // 4
    mount_height = size // 8
    mount_x = (size - mount_width) // 2
    mount_y = size // 6
    mount_coords = [mount_x, mount_y, mount_x + mount_width, mount_y + mount_height]
    draw.rectangle(mount_coords, fill=(96, 96, 96, 255), outline=(0, 0, 0, 255), width=1)
    
    return img

def main():
    """Create icon files in multiple sizes."""
    # Create icons directory
    icons_dir = "icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    # Create different sizes
    sizes = [16, 24, 32, 48, 64, 128, 256]
    
    for size in sizes:
        icon = create_webcam_icon(size)
        icon.save(f"{icons_dir}/webcam_{size}.png")
        print(f"Created {icons_dir}/webcam_{size}.png")
    
    # Create a high-quality icon for the application
    main_icon = create_webcam_icon(256)
    main_icon.save("webcam_app.png")
    print("Created webcam_app.png")
    
    # Try to create an ICO file (for Windows compatibility)
    print("Attempting to create ICO file...")
    
    try:
        # Try installing pillow with extra image format support
        import subprocess
        import sys
        print("Installing pillow with additional image format support...")
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            '--upgrade', '--force-reinstall', 'pillow'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Pillow reinstall warning: {result.stderr}")
        
        # Try creating ICO file
        print("Creating ICO file...")
        
        # Create a 32x32 icon and save as ICO (most compatible approach)
        icon_32 = create_webcam_icon(32)
        
        # Convert RGBA to RGB with white background for better Windows compatibility
        if icon_32.mode == 'RGBA':
            # Create white background
            background = Image.new('RGB', icon_32.size, (255, 255, 255))
            background.paste(icon_32, mask=icon_32.split()[-1])  # Use alpha as mask
            icon_32 = background
        
        # Try to save as ICO
        try:
            icon_32.save("webcam_app.ico", format='ICO')
            print("Successfully created webcam_app.ico (32x32)")
            
            # Verify the file was created
            if os.path.exists("webcam_app.ico"):
                file_size = os.path.getsize("webcam_app.ico")
                print(f"ICO file size: {file_size} bytes")
        
        except Exception as ico_error:
            print(f"ICO creation failed: {ico_error}")
            print("This is likely due to Pillow being compiled without ICO support")
            
            # Alternative: Create a BMP file that Windows can use as an icon
            print("Creating BMP fallback for Windows...")
            icon_32.save("webcam_app.bmp", format='BMP')
            
            # Also create a simple "fake" ICO by renaming PNG
            icon_32.save("webcam_app_icon.png", format='PNG')
            print("Created BMP and PNG alternatives for Windows")
            print("Note: Windows .spec file may need to use .bmp or .png instead of .ico")
            
    except Exception as e:
        print(f"Could not create ICO file: {e}")
        print("Using PNG icon for all platforms")

if __name__ == "__main__":
    main()
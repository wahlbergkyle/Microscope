"""
Quick test to check the actual gain range supported by your camera.
"""
import cv2
import sys

def test_gain_range():
    """Test what gain values the camera actually supports."""
    print("Testing camera gain range...")
    
    # Open the default camera (usually index 0)
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Use DirectShow on Windows
    
    if not cap.isOpened():
        print("Error: Could not open camera")
        print("(Make sure the webcam app is closed)")
        return
    
    # First set to manual mode
    print("\nSetting manual exposure mode...")
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.25)  # DirectShow manual mode
    
    # Get current gain
    current_gain = cap.get(cv2.CAP_PROP_GAIN)
    print(f"Current gain: {current_gain}")
    
    # Test various gain values
    test_values = [0.0, 0.5, 1.0, 5.0, 10.0, 25.0, 50.0, 75.0, 100.0, 128.0, 255.0]
    
    print("\nTesting gain values:")
    print("-" * 60)
    print(f"{'Set Value':<12} {'Actual Value':<15} {'Success':<10}")
    print("-" * 60)
    
    supported_values = []
    
    for test_val in test_values:
        success = cap.set(cv2.CAP_PROP_GAIN, test_val)
        actual = cap.get(cv2.CAP_PROP_GAIN)
        supported_values.append(actual)
        print(f"{test_val:<12.1f} {actual:<15.1f} {str(success):<10}")
    
    # Find the actual range
    min_gain = min(supported_values)
    max_gain = max(supported_values)
    
    print("-" * 60)
    print(f"\nActual gain range: {min_gain:.1f} to {max_gain:.1f}")
    
    # Test sub-1 values specifically
    print("\n\nTesting fractional gain values (< 1.0):")
    print("-" * 60)
    print(f"{'Set Value':<12} {'Actual Value':<15} {'Difference':<15}")
    print("-" * 60)
    
    sub_one_values = [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
    for test_val in sub_one_values:
        cap.set(cv2.CAP_PROP_GAIN, test_val)
        actual = cap.get(cv2.CAP_PROP_GAIN)
        diff = actual - test_val
        print(f"{test_val:<12.2f} {actual:<15.2f} {diff:<15.2f}")
    
    print("-" * 60)
    
    # Check if camera can actually handle values below 1
    cap.set(cv2.CAP_PROP_GAIN, 0.5)
    test_actual = cap.get(cv2.CAP_PROP_GAIN)
    
    if abs(test_actual - 0.5) < 0.1:
        print(f"\n✓ Your camera CAN handle gain values below 1.0")
        print(f"  (Setting 0.5 resulted in {test_actual:.2f})")
    elif test_actual == min_gain:
        print(f"\n✗ Your camera appears to have a minimum gain of {min_gain:.1f}")
        print(f"  (Setting 0.5 resulted in {test_actual:.2f})")
    else:
        print(f"\n? Uncertain - setting 0.5 resulted in {test_actual:.2f}")
    
    cap.release()
    print("\nTest complete!")

if __name__ == "__main__":
    try:
        test_gain_range()
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

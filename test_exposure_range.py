#!/usr/bin/env python3
import cv2
import subprocess

cap = cv2.VideoCapture(2, cv2.CAP_V4L2)
if not cap.isOpened():
    print("Can't open camera")
    exit(1)

# Set to manual mode
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

print("Trying to find exposure range by probing:")
test_values = [1, 5, 10, 50, 100, 200, 300, 400, 500, 625, 800, 1000, 1250, 2500, 5000, 10000]
for val in test_values:
    cap.set(cv2.CAP_PROP_EXPOSURE, val)
    actual = cap.get(cv2.CAP_PROP_EXPOSURE)
    print(f"  Set {val:5d} -> got {actual}")

cap.release()

print("\nUsing v4l2-ctl to get actual controls:")
result = subprocess.run(['v4l2-ctl', '-d', '/dev/video2', '-l'], 
                       capture_output=True, text=True)
if result.returncode == 0:
    for line in result.stdout.split('\n'):
        if 'exposure' in line.lower():
            print(f"  {line}")

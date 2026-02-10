#!/usr/bin/env python3
import cv2
import time

cap = cv2.VideoCapture(2, cv2.CAP_V4L2)
if not cap.isOpened():
    print("Can't open camera")
    exit(1)

print("Testing auto exposure modes:")
for mode in [0, 1, 3]:
    result = cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, mode)
    actual = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
    print(f"  Set mode {mode}: result={result}, got={actual}")

print("\nTesting exposure values with auto exposure disabled:")
# Try to set manual mode
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Manual mode for V4L2
time.sleep(0.2)

for exp_val in [-10, -7, -5, -3, -1]:
    result = cap.set(cv2.CAP_PROP_EXPOSURE, exp_val)
    actual = cap.get(cv2.CAP_PROP_EXPOSURE)
    print(f"  Set exposure {exp_val}: result={result}, got={actual}")

cap.release()

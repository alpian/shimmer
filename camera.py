import cv2.cv as cv

import time

cv.NamedWindow("camera", 1)

for i in range(2, 100):
    capture = cv.CaptureFromCAM(i)
    if capture: break

capture = cv.CaptureFromCAM(-1)

while True:
    img = cv.QueryFrame(capture)
    cv.ShowImage("camera", img)
    if cv.WaitKey(10) == 27:
        break


import os

class Camera:
    def __init__(self, number=0, path="/dev/video"):
        self.number = number
        self.path = path
        self.device = cv2.VideoCapture(0)
        assert self.device.isOpened() "Could not open video device"

    def get_frame(self):
        ret, frame = cap.read()


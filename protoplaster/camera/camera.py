from pyrav4l2 import Device, Stream
import os


class Camera:

    def __init__(self, path="/dev/video0"):
        self.path = path
        assert os.path.exists(self.path), f"Device {self.path} doesn't exist"
        self.device = Device(path)
        self.frames = iter(Stream(self.device))

    def get_frame(self):
        return next(self.frames)

    def get_device_name(self):
        return self.device.device_name

    def get_driver_name(self):
        return self.device.driver_name

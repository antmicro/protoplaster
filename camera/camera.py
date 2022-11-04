from pyrav4l2 import Device, Stream

class Camera:
    def __init__(self, path="/dev/video0"):
        self.path = path
        self.device = Device(path)
        self.frames = iter(Stream(self.device))

    def get_frame(self):
        return next(self.frames)

    def get_device_name(self):
        return self.device.device_name

    def get_driver_name(self):
        return self.device.driver_name


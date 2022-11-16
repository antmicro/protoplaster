from protoplaster.conf.module import ModuleName
from protoplaster.camera.camera import Camera


@ModuleName("camera")
class TestCamera:
    def test_frame(self):
        device = Camera(self.device)
        frame = device.get_frame()
        assert len(frame) > 0, "The frame is invalid"
        if hasattr(self, "save_file"):
            with open(self.save_file, 'wb') as file:
                file.write(frame)

    def test_device_name(self):
        device = Camera(self.device)
        assert device.get_device_name() == self.camera_name, "The device name is not correct"

    def test_driver_name(self):
        device = Camera(self.device)
        assert device.get_driver_name() == self.driver_name, "The driver name is not correct"


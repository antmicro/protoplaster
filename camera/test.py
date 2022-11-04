class TestCamera:
    def test_frame(self, device):
        assert len(device.get_frame()) > 0
    def test_device_name(self, device, camera_name):
        assert device.get_device_name() == camera_name
    def test_driver_name(self, device, driver_name):
        assert device.get_driver_name() == driver_name

class TestCamera:
    def test_frame(self, device, save_file):
        frame = device.get_frame()
        assert len(frame) > 0, "The frame is invalid"
        if save_file is not None:
            with open(save_file, 'wb') as file:
                file.write(frame)
    def test_device_name(self, device, camera_name):
        assert device.get_device_name() == camera_name, "The device name is not correct"
    def test_driver_name(self, device, driver_name):
        assert device.get_driver_name() == driver_name, "The driver name is not correct"

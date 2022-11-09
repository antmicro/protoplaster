class TestCamera:

    def test_frame(self, camera_device):
        frame = camera_device.get_frame()
        assert len(frame) > 0, "The frame is invalid"
        #if camera.save_file is not None:
        #    with open(camera.save_file, 'wb') as file:
        #        file.write(frame)

    def test_device_name(self, camera, camera_device):
        assert camera_device.get_device_name() == camera['camera_name'], "The device name is not correct"

    def test_driver_name(self, camera, camera_device):
        assert camera_device.get_driver_name() == camera['driver_name'], "The driver name is not correct"


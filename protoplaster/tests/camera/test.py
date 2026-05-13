from protoplaster.conf.module import ModuleName
from protoplaster.tests.camera.camera import Camera
import pyudev
import os
from typing import Annotated
from protoplaster.docs.docs import Hint


@ModuleName("camera")
class TestCamera:
    """
    {% macro TestCamera(device) -%}
    Camera sensor tests
    -------------------
    This module provides tests dedicated to V4L devices on specific video node: {{ label("device", device['device']) }}
    {% endmacro %}
    """
    device: Annotated[str, Hint("Video device", required=True)]
    camera_name: Annotated[str, Hint("Camera sensor name", required=True)]
    driver_name: Annotated[str, Hint("Video driver name", required=True)]
    save_file: Annotated[str, Hint("Output file for frame test")]

    def test_frame(self, record_artifact, artifacts_dir):
        """
        {% macro test_frame(device) -%}
          try to capture frame
          {%- if device['save_file'] is defined %}
            and store it to file {{ label("save_file", device['save_file']) }}
          {%- endif %}
        {%- endmacro %}
        """
        device = Camera(self.device)
        frame = device.get_frame()
        assert len(frame) > 0, "The frame is invalid"
        if hasattr(self, "save_file"):
            with open(os.path.join(artifacts_dir, self.save_file),
                      'wb') as file:
                file.write(frame)
            record_artifact(self.save_file)

    def test_device_name(self):
        """
        {% macro test_device_name(device) -%}
          check if the camera sensor name is {{ label("camera_name", device['camera_name']) }}
        {%- endmacro %}
        """
        device = Camera(self.device)
        assert device.get_device_name(
        ) == self.camera_name, "The device name is not correct"

    def test_driver_name(self):
        """
        {% macro test_driver_name(device) -%}
          check if the camera sensor driver name is {{ label("driver_name", device['driver_name']) }}
        {%- endmacro %}
        """
        device = Camera(self.device)
        assert device.get_driver_name(
        ) == self.driver_name, "The driver name is not correct"

    def camera_model(self):
        try:
            dev = pyudev.Devices.from_device_file(pyudev.Context(),
                                                  self.device)
            try:
                return dev.properties['ID_V4L_PRODUCT']
            except:
                return dev.properties['ID_MODEL']
        except:
            return None

    def name(self):
        model = self.camera_model()
        if model != None:
            return f"{model}({self.device})"
        return f"{self.device}"

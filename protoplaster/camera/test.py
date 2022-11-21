from protoplaster.conf.module import ModuleName
from protoplaster.camera.camera import Camera


@ModuleName("camera")
class TestCamera:
    """Camera sensor tests:"""

    def test_frame(self):
        """
        {% macro test_frame(camera_sensors) %}
          {% for device in camera_sensors %}
          <li>
            {{ device['device'] }}: try to capture frame
            {% if device['save_file'] is defined %}
              and store it to '{{ device['save_file'] }}' file
            {% endif %}
          </li>
          {% endfor %}
        {% endmacro %}
        """
        device = Camera(self.device)
        frame = device.get_frame()
        assert len(frame) > 0, "The frame is invalid"
        if hasattr(self, "save_file"):
            with open(self.save_file, 'wb') as file:
                file.write(frame)

    def test_device_name(self):
        """
        {% macro test_device_name(camera_sensors) %}
          {% for device in camera_sensors %}
          <li>
            {{ device['device'] }}: check if the camera sensor name is '{{ device['camera_name'] }}'
          </li>
          {% endfor %}
        {% endmacro %}
        """
        device = Camera(self.device)
        assert device.get_device_name(
        ) == self.camera_name, "The device name is not correct"

    def test_driver_name(self):
        """
        {% macro test_driver_name(camera_sensors) %}
          {% for device in camera_sensors %}
          <li>
            {{ device['device'] }}: check it the camera sensor driver name is '{{ device['driver_name'] }}'
          </li>
          {% endfor %}
        {% endmacro %}
        """
        device = Camera(self.device)
        assert device.get_driver_name(
        ) == self.driver_name, "The driver name is not correct"

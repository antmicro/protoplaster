from protoplaster.conf.module import ModuleName
import os
import pytest


@ModuleName("usbdev")
class TestUsb:

    def configure(self):
        assert hasattr(self, "device"), "'device' is an obligatory argument"
        self.sysfs_path = f"/sys/bus/usb/devices/{self.device}"

    def test_sysfs_interface(self):
        """
        {% macro test_sysfs_interface(device) -%}
          check if the sysfs interface exists: `{{ device['sysfs_path'] }}`
        {%- endmacro %}
        """
        assert os.path.exists(
            self.sysfs_path), f"USB interface {self.sysfs_path} doesn't exist"

    def test_negotiated_speed(self):
        """
        {% macro test_negotiated_speed(device) -%}
          check if the negotiated USB speed is {{ device['speed'] }} Mbps
        {%- endmacro %}
        """
        if not hasattr(self, "speed"):
            pytest.skip("speed parameter not set")

        speed_file = os.path.join(self.sysfs_path, "speed")

        assert os.path.exists(
            speed_file
        ), f"Could not find speed file: {speed_file} (is the device connected?)"

        with open(speed_file, "r") as f:
            current_speed = f.read().strip()

        assert current_speed == str(self.speed), \
            f"Expected USB speed {self.speed} Mbps, but got {current_speed} Mbps"

    def name(self):
        return f"usb({self.device})"

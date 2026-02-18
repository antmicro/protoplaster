from protoplaster.conf.module import ModuleName
import os


@ModuleName("usb")
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

    def name(self):
        return f"usb({self.device})"

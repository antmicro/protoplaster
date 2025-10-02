from protoplaster.conf.module import ModuleName
import os


@ModuleName("dac")
class TestDAC:
    """
    {% macro TestDAC(prefix) -%}
    DAC device test
    ---------------
    This module provides tests for DAC devices:
    {%- endmacro %}
    """

    def test_sysfs_interface(self):
        """
        {% macro test_sysfs_interface(device) -%}
          check if the sysfs interface exists: `{{ device['sysfs_path'] }}`
        {%- endmacro %}
        """
        assert os.path.exists(
            self.sysfs_path), "Provided DAC path doesn't exist"

    def name(self):
        return f"DAC({self.sysfs_path})"

from protoplaster.conf.module import ModuleName
import os


@ModuleName("fpga")
class TestFPGA:
    """
    {% macro TestFPGA(prefix) -%}
    Flashing FPGA test
    -----------------
    This module provides tests for flashing the fpga:
    {%- endmacro %}
    """

    def test_sysfs_interface(self):
        """
        {% macro test_sysfs_interface(device) -%}
          {% if device['sysfs_interface'] is defined -%}
            check if the sysfs interface exists: {{ device['sysfs_interface'] }}
          {%- endif %}
        {%- endmacro %}
        """
        assert os.path.exists(self.sysfs_interface)

    def test_flashing_bitstream(self):
        """
        {% macro test_flashing_bitstream(device) -%}
          {% if device['bitstream_path'] is defined -%}
            check if the bitstream {{ device['bitstream_path'] }} can be flashed to the FPGA
          {%- endif %}
        {%- endmacro %}
        """
        assert os.path.exists(f"/lib/firmware/{self.bitstream_path}"), "Bitstream file does not exist"
        with open(self.sysfs_interface, 'w') as file:
            file.write(self.bitstream_path)
        anwser = input("Did the bitstream work? [y/n] ")
        assert anwser.lower() == 'y', "The bitstream failed"

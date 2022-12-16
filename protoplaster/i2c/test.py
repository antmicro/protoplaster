from protoplaster.conf.module import ModuleName
from protoplaster.i2c.i2c import I2C


@ModuleName("i2c")
class TestI2C:
    """
    I2C devices tests
    -----------------

    This module provides tests dedicated to i2c devices on specific buses:
    """

    def test_addresses(self):
        """
        {% macro test_addresses(device) -%}
        {%- for dev in device['devices'] -%}
          {%- set addr = dev['address'] -%}
          detection test for {{ dev['name'] }} on address: 0x{{ "%0x" | format(addr|int) }}
        {%- endfor %}
        {%- endmacro %}
        """
        i2c_bus = I2C(self.bus)
        detected_addresses = i2c_bus.i2cdetect(force=True)
        for device in self.devices:
            assert device['address'] in detected_addresses

from protoplaster.conf.module import ModuleName
from protoplaster.i2c.i2c import I2C


@ModuleName("i2c")
class TestI2C:
    """
    {% macro TestI2C(prefix) -%}
    I2C devices tests
    -----------------
    {% do prefix.append('/dev/i2c-') %}
    This module provides tests dedicated to i2c devices on specific buses:
    {%- endmacro %}
    """

    def test_addresses(self):
        """
        {% macro test_addresses(device) -%}
        {%- for dev in device['devices'] -%}
          {%- set addr = dev['address'] -%}
          detection test for *{{ dev['name'] }}* on address: `0x{{ "%0x" | format(addr|int) }}`
        {%- endfor %}
        {%- endmacro %}
        """
        i2c_bus = I2C(self.bus)
        for device in self.devices:
            assert (i2c_bus.check_address(device['address'], True),
                    f"No device found at address: {device['address']}")

    def name(self):
        return f"/dev/i2c-{self.bus}" if isinstance(self.bus,
                                                    int) else self.bus

from protoplaster.conf.module import ModuleName
from protoplaster.i2c.i2c import I2C


@ModuleName("i2c")
class TestI2C:
    """ I2C tests:"""

    def test_addresses(self):
        """
        {% macro test_addresses(device) -%}
          {%- if device['bus'] is defined -%}
            bus i2c{{ device['bus'] }}: detection test for
            {%- for dev in device['devices'] -%}
              {{ " " }}{{ dev['name'] }} on address: {{ dev['address'] -}}{%- if not loop.last -%},{%- endif -%}
            {%- endfor %}
          {%- endif %}
        {%- endmacro %}
        """
        i2c_bus = I2C(self.bus)
        detected_addresses = i2c_bus.i2cdetect(force=True)
        for device in self.devices:
            assert device['address'] in detected_addresses

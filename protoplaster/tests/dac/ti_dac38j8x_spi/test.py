from protoplaster.conf.module import ModuleName
from protoplaster.tests.dac.ti_dac38j8x_spi.DAC38J8x import DAC38J8x


@ModuleName("ti_dac38j8x_spi")
class TestTiDac38j8xSpi:
    """
    {% macro TestTiDac38j8xSpi(prefix) -%}
    DAC38J8x SPI test
    ---------------
    This module provides tests for the DAC38J8x:
    {%- endmacro %}
    """

    def configure(self):
        self.dac = DAC38J8x(self.bus, self.device)

    def test_config127_value(self):
        """
        {% macro test_config127_value(device) -%}
          verify the default value of the read-only CONFIG127 register
        {%- endmacro %}
        """
        register_addr = 0x7F
        expected_value = 0x09

        read_value = self.dac.read_register(register_addr)

        assert read_value == expected_value, (
            f"Register 0x{register_addr:02X} has value 0x{read_value:02X}, "
            f"expected reset value 0x{expected_value:02X}")

    def name(self):
        return f"DAC38J8x({self.bus}, {self.device})"

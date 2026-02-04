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

    def setup_class(self):
        self.dac = DAC38J8x(self.bus, self.device)

    def test_default_values(self):
        """
        {% macro test_default_values(device) -%}
          check if read-only DAC38J8x registers have their default reset value
        {%- endmacro %}
        """

        actual = self.dac.read_register(0x7f)
        assert actual == 0x7f, (f"config127 register (= {actual:#x}) "
                                f"does not have reset value {value:#x}")

    def name(self):
        return f"DAC38J8x({self.bus}, {self.device})"

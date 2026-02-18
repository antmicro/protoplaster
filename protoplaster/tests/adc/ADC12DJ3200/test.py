from protoplaster.conf.module import ModuleName
from protoplaster.tests.adc.ADC12DJ3200.ADC12DJ3200 import ADC12DJ3200, Register


@ModuleName("ADC12DJ3200")
class TestAdc12Dj3200:
    """
    {% macro TestAdc12Dj3200(prefix) -%}
    ADC12DJ3200 SPI test
    ---------------
    This module provides tests for the ADC12DJ3200:
    {%- endmacro %}
    """

    def configure(self):
        self.adc = ADC12DJ3200(self.bus, self.device)

    def test_default_values(self):
        """
        {% macro test_default_values(device) -%}
          check if some ADC12DJ3200 registers have default reset values
        {%- endmacro %}
        """

        for reg, value in self._RESET_VALUES.items():
            actual = self.adc.read_register(reg)
            assert actual == value, (f"Register {reg.name} (= {actual:#x}) "
                                     f"does not have reset value {value:#x}")

    def name(self):
        return f"ADC12DJ3200({self.bus}, {self.device})"

    _RESET_VALUES = {
        Register.CHIP_TYPE: 0x03,
        Register.CHIP_ID: 0x0020,
        Register.CHIP_VERSION: 0x0a,
    }

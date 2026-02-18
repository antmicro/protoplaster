from protoplaster.conf.module import ModuleName
from protoplaster.tests.clock_controller.LMK04828.LMK04828 import LMK04828, Register


@ModuleName("LMK04828")
class TestLmk04828:
    """
    {% macro TestLmk04828(prefix) -%}
    LMK04828 SPI test
    ---------------
    This module provides tests for the LMK04828:
    {%- endmacro %}
    """

    def configure(self):
        self.clk = LMK04828(self.bus, self.device)

    def test_default_values(self):
        """
        {% macro test_default_values(device) -%}
          check if read-only LMK04828 registers have their default reset value
        {%- endmacro %}
        """

        for reg, value in self._RESET_VALUES.items():
            actual = self.clk.read_register(reg)
            assert actual == value, (f"Register {reg.name} (= {actual:#x}) "
                                     f"does not have reset value {value:#x}")

    def name(self):
        return f"LMK04828({self.bus}, {self.device})"

    _RESET_VALUES = {
        Register.ID_DEVICE_TYPE: 0x06,
        Register.ID_PROD: 0xd05b,
        Register.ID_MASKREV: 0x20,
        Register.ID_VNDR: 0x5104,
    }

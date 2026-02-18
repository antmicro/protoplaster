from protoplaster.conf.module import ModuleName
from protoplaster.tests.i2c_mux.TCA9548A.TCA9548A import TCA9548A
import pytest


@ModuleName("TCA9548A")
class TestTCA9548A:
    """
    {% macro TestDAC(prefix) -%}
    DAC device test
    ---------------
    This module provides tests for DAC devices:
    {%- endmacro %}
    """

    mask_after_reset = 0x0

    def configure(self):
        self.smbus_force = getattr(self, "smbus_force", False)
        self.reset_gpio = getattr(self, "reset_gpio", None)
        self.mux = TCA9548A(self.i2c_bus,
                            self.i2c_address,
                            smbus_force=self.smbus_force,
                            reset_gpio=self.reset_gpio)

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
        check if TCA9548A responds correctly to simple requests
        {%- endmacro %}
        """
        assert self.mux.is_alive(
        ), f"TCA9548A does not respond correctly. Reason: {self.mux.fail_reason}"

    def test_reset(self):
        """
        {% macro test_reset(device) -%}
        Check whether the TCA9548A responds correctly to a reset triggered by pulling {{ device['reset_gpio'] }} low
        {%- endmacro %}
        """
        if self.reset_gpio is None:
            pytest.skip("'reset_gpio' parameter not set")
        arbitrary_mask = 0xA1
        self.mux.set_mask(arbitrary_mask)
        self.mux.reset()
        current_mask = self.mux.get_mask()
        assert current_mask == TestTCA9548A.mask_after_reset, f"Reset mask mismatch: expected {hex(TestTCA9548A.mask_after_reset)}, read {hex(current_mask)}"

    def name(self):
        return f"TCA9548A({self.i2c_bus}, {hex(self.i2c_address)})"

from protoplaster.tests.adc.LTC2499.LTC2499 import LTC2499
from protoplaster.tests.adc.adc.test import TestADC
from protoplaster.conf.module import ModuleName
from protoplaster.docs.docs import Hint
from typing import Annotated


@ModuleName("LTC2499")
class TestLTC2499:
    """
    {% macro TestLTC2499(prefix) -%}
    LTC2499 device test
    ---------------
    This module provides tests for LTC2499:
    {%- endmacro %}
    """
    bus: Annotated[int | str, Hint("I2C bus")]
    address: Annotated[int, Hint("I2C address of device")]
    vref: Annotated[float, Hint("Voltage reference")]

    def configure(self) -> None:
        self.generic_test = TestADC()
        name = self.bus if isinstance(self.bus,
                                      str) else f"/dev/i2c-{self.bus}"
        self.vref = getattr(self, "vref", 5)
        self.generic_test.dev = {
            "name": name,
            "driver": "LTC2499",
            "parent": {
                "name": name,
                "driver": "I2C_SMBus",
                "bus": self.bus,
                "smbus_force": getattr(self, "smbus_force", False)
            },
            "i2c_address": self.address,
            "vref": self.vref
        }  # type: ignore
        self.generic_test.configure()

    def test_is_alive(self) -> None:
        """
        {% macro test_is_alive(device) -%}
          check if responds correctly to simple requests
        {%- endmacro %}
        """
        self.generic_test.test_is_alive()

    def name(self) -> str:
        return f"LTC2499({self.bus}, {self.address}, {self.vref})"

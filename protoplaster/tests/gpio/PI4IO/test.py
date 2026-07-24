from protoplaster.conf.module import ModuleName
from protoplaster.tests.gpio.PI4IO.PI4IO import PI4IO
from protoplaster.tests.gpio.gpio.test import TestGPIO
from protoplaster.docs.docs import Hint
from typing import Annotated


@ModuleName("PI4IO")
class TestPI4IO:
    """
    {% macro TestPI4IO(prefix) -%}
    PI4IO tests
    -----------
    This module provides tests dedicated to the PI4IOE5V96224
    {%- endmacro %}
    """

    bus: Annotated[int, Hint("I2C bus")]
    address: Annotated[int, Hint("I2C address of device")]

    def configure(self) -> None:
        self.generic_test = TestGPIO()
        name = self.bus if isinstance(self.bus,
                                      str) else f"/dev/i2c-{self.bus}"
        self.generic_test.dev = {
            "name": name,
            "model": "PI4IO",
            "parent": {
                "name": name,
                "driver": "I2C_SMBus",
                "bus": self.i2c_bus,
                "smbus_force": getattr(self, "smbus_force", False)
            },  # type: ignore
            "i2c_address": self.i2c_address,
            "reset_gpio": getattr(self, "reset_gpio", None),
            "reset_state": getattr(self, "reset_state", True),
        }
        self.generic_test.configure()

    def test_is_alive(self) -> None:
        """
        {% macro test_is_alive(device) -%}
        check if PI4IOE5V96224 responds correctly to simple requests
        {%- endmacro %}
        """
        self.generic_test.test_is_alive()

    def name(self) -> str:
        return f"PI4IO({self.bus}, {self.address})"

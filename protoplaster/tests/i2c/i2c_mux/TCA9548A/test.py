from protoplaster.conf.module import ModuleName
from protoplaster.tests.i2c.i2c.i2c import I2C
from protoplaster.tests.i2c.i2c.test import TestI2C
from protoplaster.tests.i2c.i2c_mux.TCA9548A.TCA9548A import TCA9548A
from protoplaster.tests.i2c.i2c_mux.test import TestI2CMux
from protoplaster.docs.docs import Hint
import pytest
from typing import Annotated
import importlib


@ModuleName("TCA9548A")
class TestTCA9548A:
    """
    {% macro TestTCA9548A(prefix) -%}
    TCA9548A test
    ---------------
    This module provides tests for the TCA9548A:
    {%- endmacro %}
    """

    i2c_bus: Annotated[int | str, Hint("I2C bus address", required=True)]
    i2c_address: Annotated[int, Hint("I2C device address", required=True)]
    smbus_force: Annotated[
        bool,
        Hint("Use address even if already in use by another kernel driver")]
    reset_gpio: Annotated[int | str, Hint("GPIO number for resetting device")]
    reset_state: Annotated[
        bool,
        Hint(
            "GPIO reset pin logic level -- active-low (False) or active-high (True)"
        )]

    mask_after_reset = b"\x00"

    def configure(self) -> None:
        self.generic_test = TestI2CMux()
        name = self.i2c_bus if isinstance(self.i2c_bus,
                                          str) else f"/dev/i2c-{self.i2c_bus}"
        self.generic_test.dev = {
            "name": name,
            "model": "TCA9548A",
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
        check if TCA9548A responds correctly to simple requests
        {%- endmacro %}
        """
        self.generic_test.test_is_alive()

    def test_reset(self) -> None:
        """
        {% macro test_reset(device) -%}
        Check whether the TCA9548A responds correctly to a reset triggered by pulling {{ device['reset_gpio'] }} low
        {%- endmacro %}
        """
        self.generic_test.test_reset()

    def name(self) -> str:
        return f"TCA9548A({self.i2c_bus}, {hex(self.i2c_address)})"

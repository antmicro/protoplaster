from protoplaster.conf.module import ModuleName
from protoplaster.tests.i2c.i2c import I2C
from protoplaster.docs.docs import Hint
from typing import Annotated, TypedDict


@ModuleName("i2c")
class TestI2C:
    """
    {% macro TestI2C(prefix) -%}
    I2C devices tests
    -----------------
    This module provides tests dedicated to i2c devices on specific buses:
    {%- endmacro %}
    """
    bus: Annotated[int, Hint("SMBus I2C interface", required=True)]
    __I2C_Device = TypedDict(
        "__I2C_Device", {
            "name": Annotated[str, Hint("Name of I2C device")],
            "address": Annotated[int, Hint("Address of I2C device")]
        })
    devices: Annotated[list[__I2C_Device],
                       Hint("List of I2C devices", required=True)]

    def test_addresses(self) -> None:
        """
        {% macro test_addresses(device) -%}
        detection test:
          {%- for device in self.devices or [None] %}
            * check for device {{ label("name", device.name) }} on address {{ label("address", device.address and ("0x" + ("%0x" | format(device.address|int)))) }}
          {%- endfor %}
        {%- endmacro %}
        """
        i2c_bus = I2C(self.bus)
        for device in self.devices:
            assert i2c_bus.check_address(
                device['address'],
                True), f"No device found at address: {device['address']}"

    def name(self) -> str:
        return f"/dev/i2c-{self.bus}" if isinstance(self.bus,
                                                    int) else self.bus

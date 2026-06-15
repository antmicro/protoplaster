import importlib
from protoplaster.conf.module import ModuleName
from protoplaster.tests.i2c.i2c.i2c import I2C
from typing import Annotated, TypedDict
from protoplaster.docs.docs import Hint
from protoplaster.tools.log import pr_warn


@ModuleName("i2c")
class TestI2C:
    """
    {% macro TestI2C(self) -%}
    I2C device tests
    -----------------
    This module provides tests dedicated to i2c devices on a specific bus: {{ label("dev.name", self.dev.name) }}
    {% endmacro %}
    """

    _I2C = TypedDict(
        "_I2C", {
            "name":
            Annotated[str, Hint("Name of I2C controller")],
            "driver":
            Annotated[
                str,
                Hint("Name of an I2C driver class defined in " +
                     "`protoplaster/tests/i2c` (further parameters required)")]
        })

    dev: Annotated[_I2C, Hint("I2C controller")]

    __I2C_Device = TypedDict(
        "__I2C_Device", {
            "name": Annotated[str, Hint("Name of I2C device")],
            "address": Annotated[int, Hint("Address of I2C device")]
        })

    devices: Annotated[list[__I2C_Device],
                       Hint("List of I2C devices", required=True)]

    # backward compatibility with old config format
    bus: Annotated[int | str, Hint("SMBus I2C interface", hidden=True)]

    def configure(self) -> None:
        if not hasattr(self, "dev"):
            pr_warn(
                "Parameter `dev` missing, falling back to old config format")
            bus = getattr(self, "bus")
            self.dev = {
                "driver": "I2C_SMBus",
                "bus": bus,
                "name": bus
                if isinstance(bus, str) else f"/dev/i2c-{bus}"  # type: ignore
            }
        driver_name = self.dev["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.i2c.{driver_name}.{driver_name}")
        driver = getattr(module, driver_name)
        assert issubclass(
            driver, I2C), f"Class {driver_name} must implement class 'I2C'"
        self.i2c_bus = driver(**self.dev)

    def test_addresses(self) -> None:
        """
        {% macro test_addresses(self) -%}
        detection test:
          {%- for device in self.devices or [None] %}
            * check for device {{ label("name", device.name) }} on address {{ label("address", device.address and ("0x" + ("%0x" | format(device.address|int)))) }}
          {%- endfor %}
        {%- endmacro %}
        """

        for device in self.devices:
            name = device["name"]
            addr = device.get("i2c_address") or device["address"]
            assert self.i2c_bus.check_address(
                addr
            ), f"\"{name}\" not found at address {hex(addr)}"  # type: ignore

    def name(self) -> str:
        return self.dev["name"]

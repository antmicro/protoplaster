from protoplaster.tests.gpio.gpio.gpio import GPIO, Direction
from protoplaster.tests.i2c.i2c.i2c import I2C
import importlib
from typing import Any


class GPIO_I2C(GPIO):

    def __init__(self, pins: list[int], directions: list[Direction],
                 parent: dict[str, Any], i2c_address: int):
        super().__init__(pins, directions)
        driver_name = parent["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.i2c.{driver_name}.{driver_name}")
        driver = getattr(module, driver_name)
        assert issubclass(
            driver,
            I2C), f"Class {driver_name} does not implement interface I2C"
        self.i2c_bus = driver(**parent)
        self.i2c_address = i2c_address

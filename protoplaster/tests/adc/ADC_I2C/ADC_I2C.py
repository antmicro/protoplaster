from protoplaster.tests.adc.adc.adc import ADC
from protoplaster.tests.i2c.i2c.i2c import I2C
from typing import Any
import importlib


class ADC_I2C(ADC):

    def __init__(self, parent: dict[str, Any], i2c_address: int):
        driver_name = parent["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.i2c.{driver_name}.{driver_name}")
        driver = getattr(module, driver_name)
        assert issubclass(
            driver,
            I2C), f"Class {driver_name} does not implement interface I2C"
        self.i2c_bus = driver(**parent)
        self.i2c_address = i2c_address

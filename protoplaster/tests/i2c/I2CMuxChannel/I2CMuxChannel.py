from protoplaster.tests.i2c.i2c.i2c import I2C, I2CData
from protoplaster.tests.i2c.i2c_mux.I2CMux import I2CMux
import importlib
from typing import Any


class I2CMuxChannel(I2C):

    def __init__(self, model: str, i2c_address: int, ch: int,
                 parent: dict[str, Any], **kwargs):
        mux_module = importlib.import_module(
            f"protoplaster.tests.i2c.i2c_mux.{model}.{model}")
        model_m = getattr(mux_module, model)
        assert issubclass(
            model_m, I2CMux), f"Class {model} must implement class 'I2CMux'"
        driver_name = parent["driver"]
        i2c_module = importlib.import_module(
            f"protoplaster.tests.i2c.{driver_name}.{driver_name}")
        driver = getattr(i2c_module, driver_name)
        assert issubclass(
            driver, I2C), f"Class {driver_name} must implement class 'I2C'"
        self.mux = model_m(driver(**parent), i2c_address)
        self.ch = ch

    def __enter__(self):
        self.previous_mask = self.mux.get_mask()
        self.mux.select_channel(self.ch)

    def __exit__(self):
        self.mux.set_mask(self.previous_mask)

    def read(self, address: int, length: int) -> bytes:
        return self.mux.access_i2c(self.ch).read(address, length)

    def write(self, address: int, data: I2CData) -> None:
        self.mux.access_i2c(self.ch).write(address, data)

    def exchange(self, address: int, data: I2CData, read_length: int) -> bytes:
        return self.mux.access_i2c(self.ch).exchange(address, data,
                                                     read_length)

    def check_address(self, address: int) -> bool:
        return self.mux.access_i2c(self.ch).check_address(address)

    def read_from(self, address: int, register: int) -> bytes:
        return self.mux.access_i2c(self.ch).read_from(address, register)

    def write_to(self, address: int, register: int, data: I2CData) -> None:
        return self.mux.access_i2c(self.ch).write_to(address, register, data)

from abc import ABC, abstractmethod
from protoplaster.tests.i2c.i2c.i2c import I2C
from protoplaster.tests.gpio.gpio.gpio import GPIO, Direction
from protoplaster.tests.gpio.gpio.test import TestGPIO
from typing import Any
import pytest
import importlib
import time
"""
Base class representing an I2C multiplexer device
"""


class I2CMux(ABC):

    fail_reason: str | None

    def __init__(self,
                 i2c_bus: I2C,
                 i2c_address: int,
                 reset_gpio: int | None = None,
                 reset_state: bool = True,
                 gpio_dev: TestGPIO._GPIO | None = None):
        self.bus = i2c_bus
        self.address = i2c_address
        self.reset_gpio = reset_gpio
        self.reset_state = reset_state
        self.gpio_dev = gpio_dev

    @staticmethod
    def _mask(ch: int) -> bytes:
        return (1 << ch).to_bytes()

    @abstractmethod
    def get_mask(self) -> bytes:
        pass

    @abstractmethod
    def set_mask(self, mask: bytes) -> None:
        pass

    @abstractmethod
    def is_alive(self) -> bool:
        pass

    def reset(self) -> bool:
        if self.reset_gpio is None or not self.gpio_dev:
            pytest.skip("Reset pin not configured")

        try:
            driver_name = self.gpio_dev["driver"]
            module = importlib.import_module(
                f"protoplaster.tests.gpio.{driver_name}.{driver_name}")
            driver = getattr(module, driver_name)
            assert issubclass(
                driver, GPIO), f"Class {driver_name} must implement class GPIO"
            with driver([self.reset_gpio], [Direction.OUT],
                        **self.gpio_dev) as reset_gpio:
                reset_gpio.set(self.reset_gpio, not self.reset_state)
                time.sleep(1)
                reset_gpio.set(self.reset_gpio, self.reset_state)
        except Exception as e:
            self.fail_reason = f"Error accessing rst_gpio {self.reset_gpio}: {e}"
            return False
        return True

    def select_channel(self, ch: int) -> None:
        pass

    def enable_channel(self, ch: int) -> None:
        pass

    def disable_channel(self, ch: int) -> None:
        pass

    def access_i2c(self, ch: int) -> I2C:
        self.select_channel(ch)
        return self.bus

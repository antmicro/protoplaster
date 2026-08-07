from abc import ABC, abstractmethod
from protoplaster.tests.spi.spi.spi import SPI
from typing import Any
import importlib


class Flash(ABC):

    def __init__(self, parent: dict[str, Any]) -> None:
        driver_name = parent["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.spi.{driver_name}.{driver_name}")
        driver = getattr(module, driver_name)
        assert issubclass(
            driver, SPI), f"Class {driver_name} must implement class 'SPI'"
        self.spi_bus = driver(**parent)

    @abstractmethod
    def check_presence(self) -> bool:
        pass

    @abstractmethod
    def flash(self, file_data: bytes) -> None:
        pass

    @abstractmethod
    def validate(self, file_data: bytes) -> None:
        pass

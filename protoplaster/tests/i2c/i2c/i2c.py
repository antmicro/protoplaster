from abc import ABC, abstractmethod
from typing import Iterable

I2CData = bytes | bytearray | Iterable[int]


class I2C(ABC):

    @abstractmethod
    def read(self, address: int, length: int) -> bytes:
        pass

    @abstractmethod
    def write(self, address: int, data: I2CData) -> None:
        pass

    @abstractmethod
    def exchange(self, address: int, data: I2CData, read_length: int) -> bytes:
        pass

    @abstractmethod
    def check_address(self, address: int) -> bool:
        pass

    @abstractmethod
    def read_from(self, address: int, register: int) -> bytes:
        pass

    @abstractmethod
    def write_to(self, address: int, register: int, value: I2CData) -> None:
        pass

from abc import ABC, abstractmethod
from typing import Union, Literal
from collections.abc import Collection

SPIData = Union[bytes, bytearray, Collection[int]]


class SPI(ABC):

    def __init__(self, read_command: int | None, write_command: int,
                 address_bytes: int, address_endian: Literal["little", "big"],
                 data_bytes: int, data_endian: Literal["little",
                                                       "big"]) -> None:
        self.read_command = read_command if read_command is not None else 1 << (
            address_bytes * 8 - 1)
        self.write_command = write_command
        self.address_bytes = address_bytes
        self.address_endian = address_endian
        self.data_bytes = data_bytes
        self.data_endian = data_endian

    @abstractmethod
    def write_register(self,
                       register: int,
                       value: int,
                       value_length: int | None = None) -> None:
        pass

    @abstractmethod
    def read_register(self,
                      register: int,
                      value_length: int | None = None) -> int:
        pass

    @abstractmethod
    def write(self, data: SPIData) -> None:
        pass

    @abstractmethod
    def exchange(self, data: SPIData, read_length: int) -> bytes:
        pass

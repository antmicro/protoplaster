from protoplaster.tests.spi.spi.spi import SPI, SPIData
from pyftdi.spi import SpiController
from typing import Literal


class SPI_FTDI(SPI):

    def __init__(self,
                 url: str,
                 cs_slot: int,
                 frequency: float,
                 mode: int,
                 *,
                 read_command: int | None = None,
                 write_command: int = 0,
                 address_bytes: int = 1,
                 address_endian: Literal["little", "big"] = "big",
                 data_bytes: int = 1,
                 data_endian: Literal["little", "big"] = "big",
                 **kwargs) -> None:
        super().__init__(read_command, write_command, address_bytes,
                         address_endian, data_bytes, data_endian)
        self.__spi_controller = SpiController()
        self.__spi_controller.configure(url)
        self.__port = self.__spi_controller.get_port(cs=cs_slot,
                                                     freq=frequency,
                                                     mode=mode)

    def write_register(self,
                       register: int,
                       value: int,
                       value_length: int | None = None) -> None:
        addr_cmd = register | self.write_command
        request = addr_cmd.to_bytes(self.address_bytes, self.address_endian)
        if value_length is None:
            value_length = self.data_bytes
        request += value.to_bytes(value_length, self.data_endian)
        response = self.exchange(request, 0)
        assert response is not None and len(response) == len(request)

    def read_register(self,
                      register: int,
                      value_length: int | None = None) -> int:
        addr_cmd = register | self.read_command
        request = addr_cmd.to_bytes(self.address_bytes, self.address_endian)
        if value_length is None:
            value_length = self.data_bytes
        response = self.exchange(request, value_length)
        assert response is not None and len(response) == value_length
        return int.from_bytes(response, self.data_endian)

    def write(self, data: SPIData) -> None:
        self.__port.write(data)

    def exchange(self, data: SPIData, read_length: int) -> bytes:
        return self.__port.exchange(data, read_length)

from protoplaster.tests.spi.spi.spi import SPI, SPIData
from protoplaster.tools.log import pr_warn
from typing import Literal

SPIDEV_LIBRARY = False
try:
    from spidev import SpiDev
    SPIDEV_LIBRARY = True
except ImportError:
    pr_warn("SPIDEV library is not available. Disabling spi module tests.")


class SPI_spidev(SPI):

    def __init__(self,
                 bus: int,
                 device: int,
                 *,
                 read_command: int | None = None,
                 write_command: int = 0,
                 address_bytes: int = 1,
                 address_endian: Literal["little", "big"] = "big",
                 data_bytes: int = 1,
                 data_endian: Literal["little", "big"] = "big",
                 **kwargs):
        assert SPIDEV_LIBRARY, "SPIDEV library is not available."
        super().__init__(read_command, write_command, address_bytes,
                         address_endian, data_bytes, data_endian)
        self.__dev = SpiDev(bus, device)

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

    def write_register(self,
                       register: int,
                       value: int,
                       value_length: int | None = None):
        addr_cmd = register | self.write_command
        request = addr_cmd.to_bytes(self.address_bytes, self.address_endian)
        if value_length is None:
            value_length = self.data_bytes
        request += value.to_bytes(value_length, self.data_endian)
        response = self.exchange(request, 0)
        assert response is not None and len(response) == len(request)

    def write(self, data: SPIData) -> None:
        self.exchange(data, 0)

    def exchange(self, data: SPIData, read_len: int) -> bytes:
        dummy = b"\x00" * read_len
        resp = self.__dev.xfer(bytes(data) + bytes(dummy))
        # Extra response bytes (dummy cycles) for reading data, in this case
        # only the data is returned (and not the bytes shifted out as the
        # command was being sent)
        if read_len > 0:
            return bytes(resp[len(data):])
        return resp

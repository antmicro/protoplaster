from typing import Literal

from spidev import SpiDev


class SPI:

    def __init__(self,
                 bus: int,
                 device: int,
                 read_command: int | None = None,
                 write_command=0,
                 address_bytes=1,
                 address_endian: Literal["little", "big"] = "big",
                 data_bytes=1,
                 data_endian: Literal["little", "big"] = "big"):
        self.bus = bus
        self.device = device
        self.read_command = read_command if read_command is not None else 1 << (
            address_bytes * 8 - 1)
        self.write_command = write_command
        self.address_bytes = address_bytes
        self.address_endian: Literal["little", "big"] = address_endian
        self.data_bytes = data_bytes
        self.data_endian: Literal["little", "big"] = data_endian

    def read_register(self,
                      register: int,
                      data_bytes: int | None = None) -> int:
        addr_cmd = register | self.read_command
        request = addr_cmd.to_bytes(self.address_bytes, self.address_endian)
        if data_bytes is None:
            data_bytes = self.data_bytes

        response = self.transfer(request, data_bytes)
        assert response is not None and len(response) == data_bytes
        return int.from_bytes(response, self.data_endian)

    def write_register(self,
                       register: int,
                       value: int,
                       data_bytes: int | None = None):
        addr_cmd = register | self.write_command
        request = addr_cmd.to_bytes(self.address_bytes, self.address_endian)
        if data_bytes is None:
            data_bytes = self.data_bytes
        request += value.to_bytes(data_bytes, self.data_endian)

        response = self.transfer(request)
        assert response is not None and len(response) == len(request)

    def transfer(self, data, response_bytes=0) -> bytes | None:
        dummy = b"\x00" * response_bytes
        with SpiDev(self.bus, self.device) as dev:
            resp = dev.xfer(data + dummy)
        # Extra response bytes (dummy cycles) for reading data, in this case
        # only the data is returned (and not the bytes shifted out as the
        # command was being sent)
        if response_bytes > 0:
            return bytes(resp[len(data):])
        return resp

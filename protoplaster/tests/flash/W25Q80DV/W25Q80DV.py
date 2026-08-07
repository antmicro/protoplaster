from protoplaster.tests.flash.flash.flash import Flash
import time
from typing import Any


class W25Q80DV(Flash):
    READ_ID = b"\x9f"
    JEDEC_ID = b"\xef\x40\x14"
    READ_STATUS1 = b"\x05"
    STATUS1_LEN = 1
    STATUS1_BIT_BUSY = 0
    WRITE_ENABLE = b"\x06"
    CHIP_ERASE = b"\x27"
    PAGE_PROGRAM = b"\x02"
    READ_DATA = b"\x03"
    ADDR_LEN = 3

    def __init__(self, parent: dict[str, Any], **kwargs) -> None:
        super().__init__(parent)
        self.init_address = 0
        self.page_size = 256

    def check_presence(self) -> bool:
        response = self.spi_bus.exchange(self.READ_ID, len(self.JEDEC_ID))
        return response == self.JEDEC_ID

    def __busy(self) -> bool:
        status = self.spi_bus.exchange(self.READ_STATUS1, self.STATUS1_LEN)
        status = int.from_bytes(status)
        return bool(status & (1 << self.STATUS1_BIT_BUSY))

    def __erase(self) -> None:
        self.spi_bus.write(self.WRITE_ENABLE)
        self.spi_bus.write(self.CHIP_ERASE)
        start_time = time.time()
        while self.__busy():
            assert (time.time() - start_time
                    <= 10), "Erasing failed (timeout reached)"

    def __page_program(self, addr: int, chunk: bytes) -> None:
        self.spi_bus.write(self.WRITE_ENABLE)
        address = list(addr.to_bytes(self.ADDR_LEN))
        self.spi_bus.write([int.from_bytes(self.PAGE_PROGRAM)] + address +
                           list(chunk))
        while self.__busy():
            pass

    def flash(self, file_data: bytes) -> None:
        self.__erase()
        address = self.init_address
        file_data_len = len(file_data)
        while address < file_data_len:
            chunk = file_data[address:address + self.page_size]
            self.__page_program(address, chunk)
            address += len(chunk)

    def __read(self, addr: int, read_len: int) -> bytes:
        address = list(addr.to_bytes(self.ADDR_LEN))
        return self.spi_bus.exchange([int.from_bytes(self.READ_DATA)] +
                                     address, read_len)

    def validate(self, file_data: bytes) -> None:
        address = self.init_address
        file_data_len = len(file_data)
        while address < file_data_len:
            chunk_size = min(self.page_size, file_data_len - address)
            read_data = self.__read(address, chunk_size)
            assert read_data == file_data[
                address:address +
                chunk_size], f"Flashed file data validation failed at address 0x{address:06X})"
            address += chunk_size

from enum import Enum

from protoplaster.tests.spi.spi import SPI


class Register(Enum):
    ID_DEVICE_TYPE = (0x003, 1)
    ID_PROD = (0x004, 2)
    ID_MASKREV = (0x006, 1)
    ID_VNDR = (0x00C, 2)

    def __new__(cls, index, data_bytes=1):
        obj = object.__new__(cls)
        obj._value_ = index
        obj.index = index
        obj.bytes = data_bytes
        return obj


class LMK04828:

    def __init__(self, bus, device):
        self.device = SPI(bus, device)

    def read_register(self, reg: Register):
        return self.device.read_register(reg.index, reg.bytes)

    def write_register(self, reg: Register, value):
        return self.device.write_register(reg.index, value, reg.bytes)

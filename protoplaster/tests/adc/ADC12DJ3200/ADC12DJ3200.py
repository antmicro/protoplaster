from enum import Enum

from protoplaster.tests.spi.spi import SPI


class Register(Enum):
    CONFIG_A = (0x000, 1)
    CHIP_TYPE = (0x003, 1)
    CHIP_ID = (0x004, 2)
    CHIP_VERSION = (0x006, 1)

    def __new__(cls, index, data_bytes=1):
        obj = object.__new__(cls)
        obj._value_ = index
        obj.index = index
        obj.bytes = data_bytes
        return obj


class ADC12DJ3200:

    def __init__(self, bus, device):
        self.device = SPI(bus, device)

    def read_register(self, reg: Register):
        return self.device.read_register(reg.index, reg.bytes)

    def write_register(self, reg: Register, value):
        return self.device.write_register(reg.index, value, reg.bytes)

from smbus2 import SMBus, i2c_msg
from enum import IntEnum


class TMP431Regs(IntEnum):
    CONFIGURATION = 0x3
    DEVICE_ID = 0xFD
    MANUFACTURER_ID = 0xFE
    MSB_TMP = 0x0
    LSB_TMP = 0x15


class TMP431:
    DEVICE_ID = 0x31
    MANUFACTURER_ID = 0x55

    def __init__(self,
                 i2c_bus: int,
                 i2c_address: int,
                 smbus_force: bool = False):
        self.bus = SMBus(i2c_bus, force=smbus_force)
        self.address = i2c_address

    def is_alive(self):
        try:
            if self.get_device_id() == self.DEVICE_ID and \
                self.get_manufacturer_id == self.MANUFACTURER_ID:
                return True
        except:
            pass
        return False

    def _to_int8(self, val):
        return val - 256 if val & 0x80 else val

    def read_byte_register(self, reg: int):
        return self.bus.read_byte_data(self.address, reg)

    # returns DEVICE_ID
    def get_device_id(self):
        id = self.read_byte_register(TMP431Regs.DEVICE_ID)
        return id

    # returns MANUFACTURER_ID
    def get_manufacturer_id(self):
        return self.read_byte_register(TMP431Regs.MANUFACTURER_ID)

    def configuration(self) -> int:
        conf = self.read_byte_register(TMP431Regs.CONFIGURATION)
        return conf

    def extended_range(self) -> int:
        conf = self.configuration()
        extended_range_bit = (conf >> 2) & 1
        return extended_range_bit

    def raw_to_celsius(self,
                       msb: int,
                       lsb: int,
                       extend: bool = False) -> float:
        frac = (lsb >> 4) * (1 / 16)
        if extend:
            return msb - 64 + frac
        return self._to_int8(msb) + frac

    def get_local_tmp(self):
        msb_write = i2c_msg.write(self.address, [TMP431Regs.MSB_TMP])
        msb_read = i2c_msg.read(self.address, 1)
        lsb_write = i2c_msg.write(self.address, [TMP431Regs.LSB_TMP])
        lsb_read = i2c_msg.read(self.address, 1)
        self.bus.i2c_rdwr(msb_write, msb_read, lsb_read, lsb_write)
        msb, lsb = list(msb_read)[0], list(lsb_read)[0]
        return self.raw_to_celsius(msb, lsb, self.extended_range())

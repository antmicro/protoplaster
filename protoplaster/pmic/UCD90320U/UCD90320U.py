from smbus2 import SMBus
from enum import IntEnum


class UCD90320URegs(IntEnum):
    STATUS_WORD = 0x79
    MFR_ID = 0x99
    MFR_MODEL = 0x9A
    DEVICE_ID = 0xFD


class UCD90320U:

    def __init__(self, i2c_bus, i2c_address):
        self.bus = SMBus(i2c_bus)
        self.address = i2c_address

    def is_alive(self):
        try:
            device_id_str = self.read_device_id_str()
            if device_id_str.upper().startswith("UCD90320"):
                return True
        except:
            pass
        return False

    def read_status(self):
        raw = self.bus.read_word_data(self.address, UCD90320URegs.STATUS_WORD)
        return raw

    def read_device_id_str(self):
        data = self.bus.read_block_data(self.address, UCD90320URegs.DEVICE_ID)
        return bytes(data).decode(encoding="ascii").strip("\x00 ")

    def read_mfr_id(self):
        data = self.bus.read_block_data(self.address, UCD90320URegs.MFR_ID)
        return bytes(data).decode(encoding="ascii").strip("\x00 ")

    def read_mfr_model(self):
        data = self.bus.read_block_data(self.address, UCD90320URegs.MFR_MODEL)
        return bytes(data).decode(encoding="ascii").strip("\x00 ")

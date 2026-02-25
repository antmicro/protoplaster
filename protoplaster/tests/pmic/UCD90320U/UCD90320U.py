from smbus2 import SMBus
from enum import IntEnum


class UCD90320URegs(IntEnum):
    PAGE = 0x00
    CLEAR_FAULTS = 0x03
    STATUS_WORD = 0x79  # common
    STATUS_VOUT = 0x7A  # paged
    STATUS_IOUT = 0x7B  # paged
    STATUS_TEMPERATURE = 0x7D  # paged
    STATUS_CML = 0x7E  # common
    MFR_ID = 0x99
    MFR_MODEL = 0x9A
    DEVICE_ID = 0xFD


STATUS_WORD_BITS = {
    15:
    "Output voltage fault",
    14:
    "Output current fault",
    13:
    "Input fault",
    12:
    "Manufacturer-specific",
    11:
    "Power-Good signal not asserted",
    10:
    "Fan or airflow fault",
    9:
    "Other fault",
    8:
    "Unknown fault",
    7:
    "Busy",
    6:
    "Off",
    5:
    "Output over-voltage fault",
    4:
    "Output over-current fault",
    3:
    "Input under-voltage fault",
    2:
    "Temperature fault",
    1:
    "Communication fault",
    0:
    "NONE OF THE ABOVE: A fault or warning not listed in bits [7:1] of STATUS_BYTE has occurred",
}

STATUS_VOUT_BITS = {
    7: "Output over-voltage fault",
    6: "Output over-voltage warning",
    5: "Output under-voltage warning",
    4: "Output under-voltage fault",
    3: "Attempted to configure the output voltage to an out-of-range value",
    2: "TON_MAX_FAULT",
    1: "TOFF_MAX_WARNING",
    0: "Output voltage tracking error",
}

STATUS_IOUT_BITS = {
    7: "Output over-current fault",
    6: "Output over-current and low voltage fault",
    5: "Output over-current warning",
    4: "Output under-current fault",
    3: "Current share fault",
    2: "In power limiting mode",
    1: "Output over-power fault",
    0: "Output over-power warning",
}

STATUS_TEMPERATURE_BITS = {
    7: "Over-temperature fault",
    6: "Over-temperature warning",
    5: "Under-temperature warning",
    4: "Under-temperature fault",
}

STATUS_CML_BITS = {
    7: "Invalid or unsupported command received",
    6: "Invalid or unsupported data received",
    5: "Packet error check failed",
    4: "Memory fault detected",
    3: "Processor fault detected",
    # gap
    1: "A communication fault other than the ones listed",
    0: "Other memory or logic fault",
}

_bitfields = {
    UCD90320URegs.STATUS_WORD: STATUS_WORD_BITS,
    UCD90320URegs.STATUS_VOUT: STATUS_VOUT_BITS,
    UCD90320URegs.STATUS_IOUT: STATUS_IOUT_BITS,
    UCD90320URegs.STATUS_TEMPERATURE: STATUS_TEMPERATURE_BITS,
    UCD90320URegs.STATUS_CML: STATUS_CML_BITS,
}


class UCD90320U:

    NUM_RAILS = 32

    def __init__(self,
                 i2c_bus: int,
                 i2c_address: int,
                 smbus_force: bool = False):
        self.bus = SMBus(i2c_bus, smbus_force)
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

    def set_page(self, page: int):
        assert 0 <= page < self.NUM_RAILS, f"Invalid page number {page}"
        self.bus.write_byte_data(self.address, UCD90320URegs.PAGE, page)

    def clear_faults(self):
        self.bus.write_byte(self.address, UCD90320URegs.CLEAR_FAULTS)

    def read_status_faults(self) -> list[str]:
        raw = self.bus.read_word_data(self.address, UCD90320URegs.STATUS_WORD)
        return self._decode_bitfield(raw, STATUS_WORD_BITS)

    def read_cml_faults(self) -> list[str]:
        raw = self.bus.read_word_data(self.address, UCD90320URegs.STATUS_CML)
        return self._decode_bitfield(raw, STATUS_CML_BITS)

    def read_rail_faults(self, rail: int, reg: UCD90320URegs):
        """Read a paged rail fault status register."""
        assert UCD90320URegs.STATUS_VOUT <= reg <= UCD90320URegs.STATUS_TEMPERATURE
        self.set_page(rail)
        raw = self.bus.read_byte_data(self.address, reg)
        return self._decode_bitfield(raw, _bitfields[reg])

    @staticmethod
    def _decode_bitfield(value: int, descriptions: dict[int,
                                                        str]) -> list[str]:
        active_faults = []
        for bit_pos, description in descriptions.items():
            mask = 1 << bit_pos
            if value & mask:
                active_faults.append(description)
            value &= ~mask
        if value:
            active_faults.append(f"Unknown faults: {value:#x}")
        return active_faults

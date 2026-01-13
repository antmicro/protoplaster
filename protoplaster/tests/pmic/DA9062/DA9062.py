from enum import IntEnum
from smbus2 import SMBus, i2c_msg


class DA9062Regs(IntEnum):
    PageCon0 = 0x00
    PageCon1 = 0x80
    PageCon2 = 0x100
    PageCon3 = 0x180
    FaultLog = 0x05
    LDO1Cont = 0x26
    LDO2Cont = 0x27
    LDO3Cont = 0x28
    LDO4Cont = 0x29
    DVC1 = 0x32
    VLDO1A = 0xA9
    VLDO2A = 0xAA
    VLDO3A = 0xAB
    VLDO4A = 0xAC
    VLDO1B = 0xBA
    VLDO2B = 0xBB
    VLDO3B = 0xBC
    VLDO4B = 0xBD
    DeviceId = 0x181
    VariantId = 0x182
    CustomerId = 0x183
    ConfigId = 0x184

    @staticmethod
    def LDOCont(n):
        if 1 <= n <= 4:
            return DA9062Regs(DA9062Regs.LDO1Cont + (n - 1))
        raise IndexError()

    @staticmethod
    def LDOSel(n):
        if 1 <= n <= 4:
            return DA9062Regs(DA9062Regs.LDO1Cont + (n - 1))
        raise IndexError()

    @staticmethod
    def VLDO(n, selection):
        if 1 <= n <= 4:
            if selection == LDOSelection.A:
                DA9062Regs(DA9062Regs.VLDO1A + (n - 1))
            else:
                DA9062Regs(DA9062Regs.VLDO1B + (n - 1))
        raise IndexError()


class DVC1(IntEnum):
    VBUCK1Sel = 1 << 0
    VBUCK2Sel = 1 << 1
    VBUCK3Sel = 1 << 2
    VBUCK4Sel = 1 << 3
    VLDO1Sel = 1 << 4
    VLDO2Sel = 1 << 5
    VLDO3Sel = 1 << 6
    VLDO4Sel = 1 << 7

    @classmethod
    def VLDOSel(cls, n):
        if 1 <= n <= 4:
            return cls(DVC1.VLDO1SEL + (n - 1))
        raise IndexError()


class LDOCont(IntEnum):
    LDO_EN = 0x1


class LDOSelection(IntEnum):
    A = 0x0
    B = 0x1


ldo_selection = {"A": LDOSelection.A, "B": LDOSelection.B}


class DA9062:
    DEVICE_ID = 0x62

    def __init__(self, i2c_bus, i2c_address, smbus_force):
        self.bus = SMBus(i2c_bus, force=smbus_force)
        self.i2c_address = i2c_address

    def is_alive(self):
        try:
            if self.get_device_id() == DA9062.DEVICE_ID:
                return True
        except:
            pass
        return False

    def read_register(self, reg_addr):
        page_select = 0x80
        if reg_addr >= 0x80 and reg_addr <= 0xFF:
            page_select = 0x81
        if reg_addr >= 0x100 and reg_addr <= 0x17F:
            page_select = 0x82
        if reg_addr >= 0x180 and reg_addr <= 0x1FF:
            page_select = 0x83
        # This assumes that after single read, we will go back to the page 0
        # this is enforced by 7th bit in page_select
        self.bus.write_byte_data(self.i2c_address, 0, page_select)
        return self.bus.read_byte_data(self.i2c_address, reg_addr)

    # returns DEVICE_ID
    def get_device_id(self):
        return self.read_register(DA9062Regs.DeviceId)

    def get_variant_id(self):
        return self.read_register(DA9062Regs.VariantId)

    def get_config_id(self):
        return self.read_register(DA9062Regs.ConfigId)

    def get_customer_id(self):
        return self.read_register(DA9062Regs.CustomerId)

    def get_fault_log(self):
        return self.read_register(DA9062Regs.FaultLog)

    def check_ldo_enabled(self, ldo_id):
        vldoEnabled = bool(
            self.read_register(DA9062Regs.LDOCont(ldo_id)) & LDOCont.LDO_EN)
        return vldoEnabled

    def get_ldo_curr_selection(self, ldo_id):
        selection_bit = self.read_register(
            DA9062Regs.DVC1) & DVC1.VLDOSel(ldo_id)
        selection_raw = 0 if selection_bit == 0 else 1
        vldoSelection = LDOSelection(selection_raw)
        return vldoSelection

    def get_vldo_voltage(self, ldo_id: int, selection: LDOSelection):
        step_code = self.read_register(DA9062Regs.VLDO(ldo_id, selection))
        voltage = DA9062.calc_voltage_from_step_code(step_code)
        return voltage

    def get_ldo_curr_voltage(self, ldo_id):
        selection = self.get_ldo_curr_selection(ldo_id)
        voltage = self.get_vldo_voltage(ldo_id, selection)
        return voltage

    @staticmethod
    def calc_voltage_from_step_code(step_code):
        if step_code < 0x2:
            return 0.9
        if step_code > 0x38:
            return 3.6
        return (step_code - 0x2) * 0.05 + 0.9

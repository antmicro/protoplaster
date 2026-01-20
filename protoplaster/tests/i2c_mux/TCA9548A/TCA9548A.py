from smbus2 import SMBus
from protoplaster.tests.i2c_mux.I2CMux import I2CMux


class TCA9548A(I2CMux):

    def __init__(self,
                 i2c_bus: int,
                 i2c_address: int,
                 smbus_force: bool = False):
        self.bus = SMBus(i2c_bus, force=smbus_force)
        self.address = i2c_address
        self.fail_reason = None

    def is_alive(self):
        self.fail_reason = None
        mask = 0xAA
        try:
            self.set_mask(mask)
            read_back = self.get_mask()
            if mask == read_back:
                return True
            self.fail_reason = f"Mask mismatch: written {hex(mask)}, read back {hex(read_back)}"
        except Exception as e:
            self.fail_reason = f"Error communicating with device: {e}"
        return False

    def get_mask(self) -> int:
        return self.bus.read_byte(self.address)

    def set_mask(self, mask: int) -> None:
        self._validate_mask(mask)
        self.bus.write_byte(self.address, mask)

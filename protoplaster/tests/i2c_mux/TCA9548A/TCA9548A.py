from smbus2 import SMBus
from protoplaster.tests.i2c_mux.I2CMux import I2CMux


class TCA9548A(I2CMux):

    def __init__(self, i2c_bus: int, i2c_address: int):
        self.bus = SMBus(i2c_bus)
        self.address = i2c_address

    def is_alive(self):
        mask = 0xAA
        try:
            self.set_mask(mask)
            if mask == self.get_mask():
                return True
        except:
            pass
        return False

    def get_mask(self) -> int:
        return self.bus.read_byte(self.address)

    def set_mask(self, mask: int) -> None:
        self._validate_mask(mask)
        self.bus.write_byte(self.address, mask)

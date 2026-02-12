import time
from protoplaster.tests.gpio.gpio.gpio import GPIO, Direction
from smbus2 import SMBus
from protoplaster.tests.i2c_mux.I2CMux import I2CMux


class TCA9548A(I2CMux):

    def __init__(self,
                 i2c_bus: int,
                 i2c_address: int,
                 smbus_force: bool = False,
                 reset_gpio: int = None):
        self.bus = SMBus(i2c_bus, force=smbus_force)
        self.address = i2c_address
        self.reset_gpio = reset_gpio
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

    def reset(self):
        if self.reset_gpio is None:
            return False
        try:
            with GPIO(self.reset_gpio, Direction.OUT) as reset_gpio:
                reset_gpio.write_value(0)
                time.sleep(1)  # at least 6 ns
                reset_gpio.write_value(1)
        except Exception as e:
            self.fail_reason = f"Error accessing rst_gpio {self.reset_gpio}: {e}"
            return False
        return True

    def get_mask(self) -> int:
        return self.bus.read_byte(self.address)

    def set_mask(self, mask: int) -> None:
        self._validate_mask(mask)
        self.bus.write_byte(self.address, mask)

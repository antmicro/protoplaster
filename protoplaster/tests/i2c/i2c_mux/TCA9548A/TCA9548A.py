from protoplaster.tests.i2c.i2c.i2c import I2C
from protoplaster.tests.i2c.i2c_mux.I2CMux import I2CMux
from protoplaster.tests.gpio.gpio.test import TestGPIO


class TCA9548A(I2CMux):

    def __init__(self,
                 i2c_bus: I2C,
                 i2c_address: int,
                 reset_gpio: int | None = None,
                 reset_state: bool = True,
                 gpio_dev: TestGPIO._GPIO | None = None,
                 **kwargs):
        super().__init__(i2c_bus, i2c_address, reset_gpio, reset_state,
                         gpio_dev)

    def is_alive(self) -> bool:
        self.fail_reason = None
        mask = b"\xAA"
        try:
            self.set_mask(mask)
            read_back = self.get_mask()
            if mask == read_back:
                return True
            self.fail_reason = f"Mask mismatch: written {mask.hex()}, read back {read_back.hex()}"
        except Exception as e:
            self.fail_reason = f"Error communicating with device: {e}"
        return False

    def get_mask(self) -> bytes:
        return self.bus.read(self.address, 1)

    def set_mask(self, mask: bytes) -> None:
        self._validate_mask(mask)
        self.bus.write(self.address, mask)

    def select_channel(self, ch: int) -> None:
        self._validate_channel(ch)
        self.set_mask(self._mask(ch))

    def enable_channel(self, ch: int) -> None:
        self._validate_channel(ch)
        mask_curr = int.from_bytes(self.get_mask())
        mask_ch = int.from_bytes(self._mask(ch))
        mask_new = mask_curr | mask_ch
        self.set_mask(mask_new.to_bytes())

    def disable_channel(self, ch: int) -> None:
        self._validate_channel(ch)
        mask_curr = int.from_bytes(self.get_mask())
        mask_ch = int.from_bytes(self._mask(ch))
        mask_new = mask_curr & ~mask_ch
        self.set_mask(mask_new.to_bytes())

    @staticmethod
    def _validate_channel(ch: int) -> None:
        if not (0 <= ch <= 7):
            raise IndexError

    @staticmethod
    def _validate_mask(m: bytes) -> None:
        if not (0 <= int.from_bytes(m) <= 0xFF):
            raise IndexError

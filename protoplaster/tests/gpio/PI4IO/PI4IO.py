from protoplaster.tests.gpio.gpio.gpio import Direction
from protoplaster.tests.gpio.GPIO_I2C.GPIO_I2C import GPIO_I2C
from typing import Any


class PI4IO(GPIO_I2C):

    def __init__(self, pins: list[int], directions: list[Direction],
                 parent: dict[str, Any], i2c_address: int, **kwargs) -> None:
        for pin in pins:
            self._validate_pin(pin)
        super().__init__(pins, directions, parent, i2c_address)
        self.state = [0xFF, 0xFF, 0xFF]

    def is_alive(self) -> bool:
        try:
            self._write_state()
            self._read_state()
        except:
            return False
        return True

    def _validate_pin(self, pin: int) -> None:
        if not (0 <= pin <= 24):
            raise IndexError

    def _write_state(self) -> None:
        self.i2c_bus.write(self.i2c_address, self.state)

    def _read_state(self) -> bytes:
        return self.i2c_bus.read(self.i2c_address, 3)

    def set(self, pin: int, value: bool) -> None:
        self._validate_pin(pin)
        byte_index, bit_index = divmod(pin, 8)
        if value:
            self.state[byte_index] |= (1 << bit_index)
        else:
            self.state[byte_index] &= ~(1 << bit_index)
        self._write_state()

    def get(self, pin: int) -> bool:
        self._validate_pin(pin)
        byte_index, bit_index = divmod(pin, 8)
        self.state[byte_index] |= (1 << bit_index)
        read = self._read_state()
        return bool((read[byte_index] >> bit_index) & 1)

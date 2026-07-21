from protoplaster.tests.gpio.GPIO_I2C.GPIO_I2C import GPIO_I2C
from protoplaster.tests.gpio.gpio.gpio import Direction
from typing import Any


class PCA9539(GPIO_I2C):

    __num_pins = 16
    __expander_bytes = 2
    __input_reg = [0x00, 0x01]
    __output_reg = [0x02, 0x03]
    __configuration_reg = [0x06, 0x07]

    def __init__(self, pins: list[int], directions: list[Direction],
                 parent: dict[str, Any], i2c_address: int, **kwargs) -> None:
        for n in pins:
            self._validate_pin(n)
        super().__init__(pins, directions, parent, i2c_address)
        self.outstate = [0] * self.__expander_bytes
        self.instate = [0] * self.__expander_bytes
        self.confstate = [0] * self.__expander_bytes
        self._read_conf()

    def is_alive(self) -> bool:
        try:
            self._write_state()
            self._read_state()
        except:
            return False
        return True

    def _validate_pin(self, pin: int) -> None:
        if not (0 <= pin <= self.__num_pins):
            raise IndexError

    def _write_state(self) -> None:
        for a, b in zip(self.__output_reg, self.outstate):
            self.i2c_bus.write_to(self.i2c_address, a, b.to_bytes())

    def _read_state(self) -> None:
        for i in range(self.__expander_bytes):
            state = self.i2c_bus.read_from(self.i2c_address,
                                           self.__input_reg[i])
            self.instate[i] = int.from_bytes(state)

    def _read_conf(self) -> None:
        for i, reg in enumerate(self.__configuration_reg):
            state = self.i2c_bus.read_from(self.i2c_address, reg)
            self.confstate[i] = int.from_bytes(state)

    def _write_conf(self) -> None:
        for reg, data in zip(self.__configuration_reg, self.confstate):
            self.i2c_bus.write_to(self.i2c_address, reg, data.to_bytes())

    def set(self, pin: int, value: bool) -> None:
        byte_index, bit_index = divmod(pin, 8)
        # set pin as output
        self.confstate[byte_index] &= ~(1 << bit_index)
        self._write_conf()
        self._read_conf()
        # confirm
        assert not (self.confstate[byte_index] &
                    (1 << bit_index)), f"Could not set pin {pin} as output"
        if value:
            self.outstate[byte_index] |= (1 << bit_index)
        else:
            self.outstate[byte_index] &= ~(1 << bit_index)
        self._write_state()

    def get(self, pin: int) -> bool:
        byte_index, bit_index = divmod(pin, 8)
        self._read_state()
        return bool((self.instate[byte_index] >> bit_index) & 1)

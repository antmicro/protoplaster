from smbus2 import SMBus, i2c_msg


class PI4IOE5V96224:

    def __init__(self, i2c_bus: int, i2c_address: int):
        self.bus = SMBus(i2c_bus)
        self.address = i2c_address
        self.state = [0xFF, 0xFF, 0xFF]

    def is_alive(self):

        try:
            self._write_state()
            self._read_state()
        except:
            return False
        return True

    def _validate_pin(self, pin: int) -> None:
        if not (0 <= pin <= 24):
            raise IndexError

    def _write_state(self):
        msg = i2c_msg.write(self.address, self.state)
        self.bus.i2c_rdwr(msg)

    def _read_state(self):
        msg = i2c_msg.read(self.address, 3)
        self.bus.i2c_rdwr(msg)
        return list(msg)

    def set_pin(self, pin: int, value: int):
        self._validate_pin(pin)
        byte_index, bit_index = divmod(pin, 8)
        if value:
            self.state[byte_index] |= (1 << bit_index)
        else:
            self.state[byte_index] &= ~(1 << bit_index)
        self._write_state()

    # pin should be beforehand set to 1
    def get_pin(self, pin: int) -> int:
        self._validate_pin(pin)
        byte_index, bit_index = divmod(pin, 8)
        self.state[byte_index] |= (1 << bit_index)
        read = self._read_state()
        return (read[byte_index] >> bit_index) & 1

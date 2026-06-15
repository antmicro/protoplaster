from protoplaster.tests.i2c.i2c.i2c import I2C, I2CData
from smbus2 import SMBus, i2c_msg


class I2C_SMBus(I2C):

    ADDR_MIN = 0x03
    ADDR_MAX = 0x77

    def __init__(self, bus: int | str, smbus_force: bool = False, **kwargs):
        self.bus = SMBus(bus, force=smbus_force)

    def read(self, address: int, length: int) -> bytes:
        read_cmd = i2c_msg.read(address, length)
        self.bus.i2c_rdwr(read_cmd)
        return bytes(read_cmd)

    def write(self, address: int, data: I2CData) -> None:
        write_cmd = i2c_msg.write(address, data)
        self.bus.i2c_rdwr(write_cmd)

    def exchange(self, address: int, data: I2CData, read_length: int) -> bytes:
        write_cmd = i2c_msg.write(address, data)
        read_cmd = i2c_msg.read(address, read_length)
        self.bus.i2c_rdwr(write_cmd, read_cmd)
        return bytes(read_cmd)

    def check_address(self, address: int, force: bool = False) -> bool:
        try:
            self.bus.read_byte(address, force=force)
            return True
        except OSError:
            return False

    def i2cdetect(self, force: bool = False) -> list[int]:
        detected_addresses = []
        for address in range(I2C_SMBus.ADDR_MIN, I2C_SMBus.ADDR_MAX + 1):
            if self.check_address(address, force=force):
                detected_addresses.append(address)
        return detected_addresses

    def read_from(self, address: int, register: int) -> bytes:
        return self.bus.read_byte_data(address, register)

    def write_to(self, address: int, register: int, value: I2CData) -> None:
        self.bus.write_byte_data(address, register, value)

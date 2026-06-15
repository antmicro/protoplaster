from protoplaster.tests.i2c.i2c.i2c import I2C, I2CData
from pyftdi.i2c import I2cController


class I2C_FTDI(I2C):

    def __init__(self, url: str, **kwargs) -> None:
        self.url = url
        self.__i2c_controller = I2cController()
        self.__i2c_controller.set_retry_count(1)
        self.__i2c_controller.configure(self.url)

    def read(self, address: int, length: int) -> bytes:
        return self.__i2c_controller.get_port(address).read(length)

    def write(self, address: int, data: I2CData) -> None:
        self.__i2c_controller.get_port(address).write(data)

    def exchange(self, address: int, data: I2CData, read_length: int) -> bytes:
        return self.__i2c_controller.get_port(address).exchange(
            data, read_length)

    def check_address(self, address: int) -> bool:
        return self.__i2c_controller.get_port(address).poll(True)

    def read_from(self, address: int, register: int) -> bytes:
        return self.__i2c_controller.get_port(address).read_from(register, 1)

    def write_to(self, address: int, register: int, value: I2CData) -> None:
        return self.__i2c_controller.get_port(address).write_to(
            register, value)

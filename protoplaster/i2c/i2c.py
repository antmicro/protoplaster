from smbus2 import SMBus

class I2C:
    def __init__(self, bus):
        self.bus = SMBus(bus)

    def check_address(self, address, force=False):
        try:
            self.bus.read_byte(address, force=force)
            return True
        except OSError:
            return False

    def i2cdetect(self, force=False):
        detected_addresses = []
        for address in range(0x03, 0x78):
            if self.check_address(address, force=force):
                detected_addresses.append(address)
        return detected_addresses

    def read_data(self, address, register=0, force=False):
        return self.bus.read_byte_data(address, register, force=force)

    def write_data(self, address, value, register=0, force=False):
        return self.bus.write_byte_data(address, register, value, force=force)


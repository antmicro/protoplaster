from protoplaster.tests.spi.SPI_spidev.SPI_spidev import SPI_spidev


class DAC38J8x:

    def __init__(self, bus, device):
        self.device = SPI_spidev(bus, device, data_bytes=2)

    def read_register(self, reg):
        return self.device.read_register(reg)

    def write_register(self, reg, value):
        return self.device.write_register(reg, value)

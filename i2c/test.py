import i2c

class TestI2C:
    def test_addresses(self, bus, addresses):
        i2c_bus = i2c.I2C(bus)
        detected_addresses = i2c_bus.i2cdetect(force=True)
        for addr in addresses:
            assert addr in detected_addresses


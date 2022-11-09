from i2c.i2c import I2C

class TestI2C:
    def test_addresses(self, bus, addresses):
        i2c_bus = I2C(bus)
        detected_addresses = i2c_bus.i2cdetect(force=True)
        for addr in addresses:
            assert addr in detected_addresses


from protoplaster.conf.module import ModuleName
from protoplaster.i2c.i2c import I2C


@ModuleName("i2c")
class TestI2C:
    def test_addresses(self):
        i2c_bus = I2C(self.bus)
        detected_addresses = i2c_bus.i2cdetect(force=True)
        for addr in self.addresses:
            assert addr in detected_addresses


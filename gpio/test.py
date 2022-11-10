from conf.module import ModuleName
from gpio.gpio import GPIO, Direction


@ModuleName("gpio")
class TestGPIO:
    def test_read_write(self):
        with GPIO(self.number, Direction.OUT) as gpio:
            gpio.write_value(self.value)
            assert gpio.read_value() == self.value


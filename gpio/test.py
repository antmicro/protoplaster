from gpio import GPIO, Direction

class TestGPIO:
    def test_read_write(self, number, value):
        with GPIO(number, Direction.OUT) as gpio:
            gpio.write_value(value)
            assert gpio.read_value() == value


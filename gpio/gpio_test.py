from gpio import GPIO

def test_read(pin):
    with GPIO(pin) as gpio:
        assert gpio.read_value() == '0'


import os


class ADC:

    def __init__(self, path="/sys/bus/iio/devices/iio:device0"):
        self.path = path

    def is_alive(self):
        return os.path.exists(self.path)

    def read_adc(self, channel=0):
        with open(f"{self.path}/in_voltage{channel}_raw", "r") as f:
            raw = int(f.read())
        with open(f"{self.path}/in_voltage{channel}_scale", "r") as f:
            scale = float(f.read())
        voltage = raw * scale
        return voltage

    def get_device_name(self):
        with open(f"{self.path}/name", "r") as f:
            name = f.read()
        return name

    def get_device_numbers(self):
        with open(f"{self.path}/dev", "r") as f:
            devnum_str = f.read()  # e.g. 248:0
        device_number = [int(num) for num in devnum_str.split(":")]

        return device_number

from protoplaster.tests.adc.adc.adc import ADC
import os


class ADC_IIO(ADC):

    def __init__(self,
                 path: str = "/sys/bus/iio/devices/iio:device0",
                 **kwargs):
        self.path = path

    def is_alive(self) -> bool:
        return os.path.exists(self.path)

    def read_adc(self, channel: int) -> int:
        with open(f"{self.path}/in_voltage{channel}_raw", "r") as f:
            raw = int(f.read())
        return raw

    def convert_voltage(self, raw: int, **kwargs) -> float:
        with open(f"{self.path}/in_voltage{kwargs['channel']}_scale",
                  "r") as f:
            scale = float(f.read())
        voltage = raw * scale
        return voltage

    def get_device_name(self) -> str:
        with open(f"{self.path}/name", "r") as f:
            name = f.read()
        return name

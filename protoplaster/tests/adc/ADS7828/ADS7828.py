from protoplaster.tests.adc.adc.adc import ADC
from protoplaster.tests.adc.ADC_I2C.ADC_I2C import ADC_I2C
from typing import Any


class ADS7828(ADC_I2C):

    __control_bytes = {
        0: 0b10001100,
        1: 0b11001100,
        2: 0b10011100,
        3: 0b11011100,
        4: 0b10101100,
        5: 0b11101100,
        6: 0b10111100,
        7: 0b11111100,
    }
    # the first reading after ADC is activated will be slightly off and should be discarded
    __read_attempts = 2
    __value_bytes = 2

    def __init__(self, parent: dict[str,
                                    Any], i2c_address: int, r_div_lower: float,
                 r_div_upper: float, vref: float, resolution: float, **kwargs):
        super().__init__(parent, i2c_address)
        self.r_div_lower = r_div_lower
        self.r_div_upper = r_div_upper
        self.vref = vref
        self.resolution = resolution

    def is_alive(self) -> bool:
        return self.i2c_bus.check_address(self.i2c_address)

    def read_adc(self, channel: int) -> int:
        for i in range(self.__read_attempts):
            read = self.i2c_bus.exchange(self.i2c_address,
                                         [self.__control_bytes[channel]],
                                         self.__value_bytes)
        return int.from_bytes(read, byteorder="big")

    def convert_voltage(self, raw: int, **kwargs) -> float:
        r_upper = kwargs.get("r_div_upper_ext", 0) + self.r_div_upper
        resistor_voltage_divider = (r_upper +
                                    self.r_div_lower) / (self.r_div_lower)
        adc_lsb_voltage = self.vref / self.resolution
        return raw * resistor_voltage_divider * adc_lsb_voltage

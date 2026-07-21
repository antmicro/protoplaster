from protoplaster.tests.adc.adc.adc import ADC
from protoplaster.tests.adc.ADC_I2C.ADC_I2C import ADC_I2C
from abc import abstractmethod
from typing import Any


class LTC249_(ADC_I2C):

    def __init__(self,
                 parent: dict[str, Any],
                 i2c_address: int,
                 vref: float = 5,
                 **kwargs) -> None:
        super().__init__(parent, i2c_address)
        self.vref = vref
        self.config_word: list[int] | None = None

    @property
    @abstractmethod
    def ch_sel(self):
        pass

    def is_alive(self) -> bool:
        self.fail_reason = None

        try:
            self.start_conversion()
        except Exception as e:
            self.fail_reason = f"Device did not respond to start_conversion: {e}"
            return False

        # at most 2 bytes can be written, 3rd is never acked
        acknowledged3rdbyte = True
        try:
            self.i2c_bus.write(self.i2c_address, [0b101 << 5, 0xFF, 0xFF])
        except:
            acknowledged3rdbyte = False
        if acknowledged3rdbyte:
            self.fail_reason = "Device acknowledged 3rd byte during write"
            return False

        # at most 4 bytes can be read, 5th is never acked
        acked_read_cmd = True
        try:
            self.i2c_bus.read(self.i2c_address, 5)
        except:
            acked_read_cmd = False
        if acked_read_cmd:
            self.fail_reason = "Device acknowledged 5th byte during read"
            return False
        return True

    # When the device is addressed during the conversion state, it will
    # not acknowledge R/W requests and will issue a NACK by
    # leaving the SDA line high.
    def read_raw(self) -> int:
        read_bytes = self.i2c_bus.read(self.i2c_address, 4)
        read = int.from_bytes(read_bytes, byteorder="big")
        return read

    def write_config(self) -> None:
        self.i2c_bus.write(self.i2c_address, self.config_word)

    def configure_channel(self,
                          sgl: int = 1,
                          odd: int = 0,
                          a2: int = 0,
                          a1: int = 0,
                          a0: int = 0,
                          en2: int = 0,
                          im: int = 0,
                          fa: int = 1,
                          fb: int = 1,
                          spd: int = 0) -> None:
        # preamble 101 = write config
        control_high = (0b101 << 5) | (sgl << 4) | (odd << 3) | (a2 << 2) | (
            a1 << 1) | a0
        control_low = (en2 << 7) | (im << 6) | (fa << 5) | (fb << 4) | (
            spd << 3)

        self.config_word = [control_high, control_low]

    def start_conversion_on(self, ch: int) -> None:
        # start conversion on channel ch
        # reject 50Hz/60Hz
        # 1x mode
        additional_config = [1, 0, 1, 1, 0]
        self.configure_channel(*(self.ch_sel[ch]), *additional_config)
        self.write_config()

    # always after full read next conversion is started with previous configuration
    # therefore its mostly dummy write to start new conversion without reading previous one
    def start_conversion(self) -> None:
        control_high = (0b100 << 5)
        control_low = 0
        # keeps previous configuration
        self.i2c_bus.write(self.i2c_address, [control_high, control_low])

    def read_adc(self, channel: int) -> int:
        self.start_conversion_on(channel)
        return self.read_raw()

    def convert_voltage(self, raw: int, **kwargs) -> float:
        FS = self.vref / 2
        sig = (raw >> 31) & 1
        msb = (raw >> 30) & 1
        assert not (sig == 1 and msb == 1), f"Voltage out of range ({FS})"
        assert not (sig == 0 and msb == 0), f"Voltage out of range ({-FS})"
        res = (raw >> 6) & 0x0FFFFFF
        if (raw >> 6) & 0x800000:
            res -= 0x8000000 * 2
        voltage = (res / (1 << 23)) * FS
        return voltage

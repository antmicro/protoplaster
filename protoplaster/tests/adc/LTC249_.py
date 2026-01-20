from smbus2 import SMBus, i2c_msg
from abc import ABC, abstractmethod


class LTC249_(ABC):

    def __init__(self, i2c_bus, address, vref=5):
        self.bus = SMBus(i2c_bus)
        self.address = address
        self.vref = vref
        self.config_word = None
        self.fail_reason = None

    @property
    @abstractmethod
    def ch_sel(self):
        pass

    def is_alive(self):
        self.fail_reason = None

        try:
            self.start_conversion()
        except Exception as e:
            self.fail_reason = f"Device did not respond to start_conversion: {e}"
            return False

        # at most 2 bytes can be written, 3th is never acked
        acknowledged3thbyte = True
        try:
            write_cmd = i2c_msg.write(self.address, [0b101 << 5, 0xFF, 0xFF])
            self.bus.i2c_rdwr(write_cmd)
        except:
            acknowledged3thbyte = False
        if acknowledged3thbyte:
            self.fail_reason = "Device acknowledged 3rd byte during write"
            return False

        # at most 4 bytes can be read, 5th is never acked
        acked_read_cmd = True
        try:
            read_cmd = i2c_msg.read(self.address, 5)
            self.bus.i2c_rdwr(read_cmd)
        except:
            acked_read_cmd = False
        if acked_read_cmd:
            self.fail_reason = "Device acknowledged 5th byte during read"
            return False
        return True

    # When the device is addressed during the conversion state, it will
    # not acknowledge R/W requests and will issue a NACK by
    # leaving the SDA line high.
    def read_raw(self):
        read_cmd = i2c_msg.read(self.address, 4)
        self.bus.i2c_rdwr(read_cmd)
        read_arr = list(read_cmd)
        read = int.from_bytes(read_arr, byteorder="big")
        return read

    def write_config(self):
        write_cmd = i2c_msg.write(self.address, self.config_word)
        self.bus.i2c_rdwr(write_cmd)

    def configure_channel(self,
                          sgl=1,
                          odd=0,
                          a2=0,
                          a1=0,
                          a0=0,
                          en2=0,
                          im=0,
                          fa=1,
                          fb=1,
                          spd=0):
        # preamble 101 = write config
        control_high = (0b101 << 5) | (sgl << 4) | (odd << 3) | (a2 << 2) | (
            a1 << 1) | a0
        control_low = (en2 << 7) | (im << 6) | (fa << 5) | (fb << 4) | (
            spd << 3)

        self.config_word = [control_high, control_low]

    def start_conversion_on(self, ch):
        # start convertion on channel ch
        # reject 50Hz/60Hz
        # 1x mode
        additional_config = [1, 0, 1, 1, 0]
        self.configure_channel(*(self.ch_sel[ch]), *additional_config)
        self.write_config()

    # always after full read next conversion is started with previous configuration
    # therefore its mostly dummy write to start new conversion without reading previous one
    def start_conversion(self):
        control_high = (0b100 << 5)
        control_low = 0
        # keeps previous configuration
        keep_previous_cmd = i2c_msg.write(self.address,
                                          [control_high, control_low])
        self.bus.i2c_rdwr(keep_previous_cmd)

    def read_voltage(self):
        raw = self.read_raw()
        FS = self.vref / 2
        sig = (raw >> 31) & 1
        msb = (raw >> 30) & 1
        if sig == 1 and msb == 1:
            return ('over_range', FS)
        if sig == 0 and msb == 0:
            return ('under_range', -FS)
        res = (raw >> 6) & 0x0FFFFFF
        if (raw >> 6) & 0x800000:
            res -= 0x8000000 * 2
        voltage = (res / (1 << 23)) * FS
        return ('voltage', voltage)

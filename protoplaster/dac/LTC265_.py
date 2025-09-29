from smbus2 import SMBus, i2c_msg
from math import floor
from abc import abstractmethod, ABC


# LTC265_ are write-only peripherals
# therefore they don't ack read cmds
class LTC265_(ABC):

    def __init__(self, i2c_bus, i2c_address, vref=5, N=16):
        self.bus = SMBus(i2c_bus)
        self.address = i2c_address
        self.vref = vref
        self.N = N

    @property
    @abstractmethod
    def dac_addr(self):
        pass

    def is_alive(self):
        # test if device responds at all
        try:
            self.write_do_nothing()
        except:
            return False
        # at most 3 bytes can be written, 4th is never acked
        acknowledged4thbyte = True
        try:
            write_cmd = i2c_msg.write(self.address, [0xFF, 0xFF, 0xFF, 0xFF])
            self.bus.i2c_rdwr(write_cmd)
        except:
            acknowledged4thbyte = False
        if acknowledged4thbyte:
            return False

        # peripheral is read only and never acks read req
        acked_read_cmd = True
        try:
            read_cmd = i2c_msg.read(self.address, 1)
            self.bus.i2c_rdwr(read_cmd)
        except:
            acked_read_cmd = False
        if acked_read_cmd:
            return
        return True

    def write_do_nothing(self):
        # do nothing cmd
        cmd = 0xFF

        # arbitrary data passed to do nothing cmd
        msb = 0x0
        lsb = 0x0
        self.write_raw(cmd, msb, lsb)

    def volts2bytes(self, volts: float):
        tick = floor(volts * (2**self.N) / 2 / self.vref)
        msb = (tick >> 8) & 0xFF
        lsb = tick & 0xFF
        return [msb, lsb]

    # sets voltage in volts on ch channel, rounding to lower tick
    def set_voltage(self, ch: str, v: float):
        cmd = 0b0011 << 4 | self.dac_addr[ch]
        msb, lsb = self.volts2bytes(v)
        self.write_raw(cmd, msb, lsb)

    def write_raw(self, cmd, msb, lsb):
        self.config = [cmd, msb, lsb]
        write_cmd = i2c_msg.write(self.address, self.config)

        self.bus.i2c_rdwr(write_cmd)

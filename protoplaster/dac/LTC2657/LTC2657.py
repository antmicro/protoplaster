from protoplaster.dac.LTC265_ import LTC265_


class LTC2657(LTC265_):

    @property
    def dac_addr(self):
        return {
            "A": 0b0000,
            "B": 0b0001,
            "C": 0b0010,
            "D": 0b0011,
            "E": 0b0100,
            "F": 0b0101,
            "G": 0b0110,
            "H": 0b0111,
            "all": 0b1111
        }

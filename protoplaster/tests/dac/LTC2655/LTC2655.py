from protoplaster.tests.dac.LTC265_ import LTC265_


class LTC2655(LTC265_):

    @property
    def dac_addr(self):
        return {
            "A": 0b0000,
            "B": 0b0001,
            "C": 0b0010,
            "D": 0b0011,
            "all": 0b1111
        }

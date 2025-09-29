from protoplaster.adc.LTC249_ import LTC249_


class LTC2493(LTC249_):

    @property
    def ch_sel(self):
        return [[1, 0, 0, 0, 0], [1, 1, 0, 0, 0], [1, 0, 0, 0, 1],
                [1, 1, 0, 0, 1]]

from abc import ABC, abstractmethod


class I2CMux(ABC):

    def _mask(ch: int):
        return 1 << ch

    @abstractmethod
    def get_mask(self) -> int:
        pass

    @abstractmethod
    def set_mask(self, mask: int) -> None:
        pass

    def select_channel(self, ch: int) -> None:
        self._validate_channel(ch)
        self.set_mask(self._mask(ch))

    def enable_channel(self, ch: int) -> None:
        self._validate_channel(ch)
        mask = self.get_mask()
        self.set_mask(mask | self._mask(ch))

    def disable_channel(self, ch: int) -> None:
        self._validate_channel(ch)
        mask = self.get_mask()
        self.set_mask(mask & ~self._mask(ch))

    def channel(self, ch: int):
        return I2CMuxChannel(self, ch)

    @staticmethod
    def _validate_channel(ch: int) -> None:
        if not (0 <= ch <= 7):
            raise IndexError

    @staticmethod
    def _validate_mask(m: int) -> None:
        if not (0 <= m <= 0xFF):
            raise IndexError


class I2CMuxChannel:

    def __init__(self, mux: I2CMux, ch: int):
        self.mux = mux
        self.ch = ch

    def __enter__(self):
        self.previous_mask = self.mux.get_mask()
        self.mux.select_channel(self.ch)

    def __exit__(self):
        self.mux.set_mask(self.previous_mask)

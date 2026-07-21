from abc import ABC, abstractmethod


class ADC(ABC):

    @abstractmethod
    def is_alive(self) -> bool:
        pass

    @abstractmethod
    def read_adc(self, channel: int) -> int:
        pass

    @abstractmethod
    def convert_voltage(self, raw: int, **kwargs) -> float:
        pass

from enum import Enum
from abc import ABC, abstractmethod


class Direction(Enum):
    IN = "in"
    OUT = "out"


class GPIO(ABC):

    def __init__(self, pins: list[int], directions: list[Direction]):
        self.pins = pins
        self.dirs = [Direction(d) for d in directions]

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        return

    def get_pins(self) -> list[int]:
        return self.pins

    def get_dirs(self) -> list[Direction]:
        return self.dirs

    @abstractmethod
    def get(self, pin: int) -> bool:
        pass

    @abstractmethod
    def set(self, pin: int, value: bool) -> None:
        pass

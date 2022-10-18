from enum import Enum
import os


class Direction(Enum):
    IN = "in"
    OUT = "out"


class GPIO:
    def __init__(self, number, direction: Direction = Direction.IN, path="/sys/class/gpio"):
        self.number = number
        self.direction = direction
        self.path = path

    def __enter__(self):
        self.export()
        return self

    def __exit__(self, *args, **kwargs):
        self.unexport()

    def export(self):
        assert os.path.isfile(f"{self.path}/export"), "Sysfs interface for GPIO does not exist"
        with open(f"{self.path}/export", 'w') as file:
            file.write(str(self.number))
        assert os.path.isdir(f"{self.path}/gpio{self.number}"), "GPIO could not be initiated"
        with open(f"{self.path}/gpio{self.number}/direction", 'w') as file:
            file.write(self.direction.value)
        return self

    def unexport(self):
        with open(f"{self.path}/unexport", 'w') as file:
            file.write(str(self.number))

    def read_value(self):
        with open(f"{self.path}/gpio{self.number}/value") as file:
            value = file.read()
        return value.strip()

    def write_value(self, value):
        assert self.direction == Direction.OUT, "You can only write to a GPIO in an OUT state"
        with open(f"{self.path}/gpio{self.number}/value", 'w') as file:
            file.write(str(value))



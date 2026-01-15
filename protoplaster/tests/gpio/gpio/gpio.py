from enum import Enum
import os


class Direction(Enum):
    IN = "in"
    OUT = "out"


class GPIO:

    def __init__(self,
                 number,
                 direction: Direction = Direction.IN,
                 path="/sys/class/gpio",
                 gpio_name=None):
        self.number = number
        self.direction = direction
        self.path = path
        self.gpio_name = gpio_name if gpio_name is not None else f"gpio{number}"
        self.unexport_gpio = True

    def __enter__(self):
        self.export()
        return self

    def __exit__(self, *args, **kwargs):
        if self.unexport_gpio:
            self.unexport()

    def export(self):
        if not os.path.isdir(f"{self.path}/{self.gpio_name}"):
            assert os.path.isfile(f"{self.path}/export"
                                  ), "Sysfs interface for GPIO does not exist"
            with open(f"{self.path}/export", 'w') as file:
                file.write(str(self.number))
            self.unexport_gpio = True
        else:
            self.unexport_gpio = False
        assert os.path.isdir(
            f"{self.path}/{self.gpio_name}"), "GPIO could not be initiated"
        with open(f"{self.path}/{self.gpio_name}/direction", 'w') as file:
            file.write(self.direction.value)
        return self

    def unexport(self):
        with open(f"{self.path}/unexport", 'w') as file:
            file.write(str(self.number))

    def read_value(self):
        with open(f"{self.path}/{self.gpio_name}/value") as file:
            value = file.read()
        return int(value.strip())

    def write_value(self, value):
        assert self.direction == Direction.OUT, "You can only write to a GPIO in an OUT state"
        with open(f"{self.path}/{self.gpio_name}/value", 'w') as file:
            file.write(str(value))

import os
from protoplaster.tests.gpio.gpio.gpio import GPIO, Direction
from itertools import zip_longest


class GPIO_sysfs(GPIO):

    def __init__(self,
                 gpio_numbers: list[int],
                 directions: list[Direction],
                 sysfs_gpio_path: str = "/sys/class/gpio",
                 gpio_names: list[str] = [],
                 export: bool = False,
                 **kwargs):
        self.gpio_names = [
            name or f"gpio{num}"
            for name, num in zip_longest(gpio_names, gpio_numbers)
        ]
        super().__init__(gpio_numbers, directions)
        self.path = sysfs_gpio_path
        assert os.path.isfile(
            f"{self.path}/export"), "Sysfs interface for GPIO does not exist"
        self.exported_initially = [
            os.path.isdir(f"{self.path}/{pin}") for pin in self.gpio_names
        ]
        if export:
            self.export()

    def __enter__(self):
        self.export()
        return self

    def __exit__(self, *args, **kwargs):
        if self.unexport_gpio:
            self.unexport()

    def export(self):
        for i in range(len(self.gpio_names)):
            if self.exported_initially[i]:
                continue
            name = self.gpio_names[i]
            num = super().get_pins()[i]
            direction = super().get_dirs()[i]
            with open(f"{self.path}/export", "w") as file:
                file.write(str(num))
            assert os.path.isdir(
                f"{self.path}/{name}"), f"GPIO {name} could not be initiated"
            with open(f"{self.path}/{name}/direction", "w") as file:
                file.write(direction.value)
        return self

    def unexport(self):
        for num, leave_exported in zip(super().get_pins(),
                                       self.exported_initially):
            if leave_exported:
                continue
            with open(f"{self.path}/unexport", 'w') as file:
                file.write(str(num))

    def get(self, number: int) -> bool:
        idx = super().get_pins().index(number)
        assert os.path.isdir(f"{self.path}/{self.gpio_names[idx]}"
                             ), f"GPIO pin {self.gpio_names[idx]} not exported"
        with open(f"{self.path}/{self.gpio_names[idx]}/value") as file:
            value = file.read()
        return bool(value.strip())

    def set(self, number: int, value: bool) -> None:
        idx = super().get_pins().index(number)
        assert os.path.isdir(f"{self.path}/{self.gpio_names[idx]}"
                             ), f"GPIO pin {self.gpio_names[idx]} not exported"
        assert super().get_dirs(
        )[idx] == Direction.OUT, "You can only write to a GPIO in an OUT state"
        with open(f"{self.path}/{self.gpio_names[idx]}/direction",
                  'r') as file:
            assert file.read().strip(
            ) == "out", f"GPIO pin {self.gpio_names[idx]} is not set as output in the kernel"
        with open(f"{self.path}/{self.gpio_names[idx]}/value", 'w') as file:
            file.write(str(int(value)))

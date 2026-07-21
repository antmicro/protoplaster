from protoplaster.conf.module import ModuleName
from protoplaster.tests.gpio.gpio.gpio import GPIO, Direction
import importlib
import pytest
import time
from typing import Annotated, TypedDict
from protoplaster.docs.docs import Hint
from protoplaster.tools.log import pr_warn


@ModuleName("gpio")
class TestGPIO:
    """
    {% macro TestGPIO(self) -%}
    GPIOs tests
    -----------
    This module provides tests dedicated to GPIO on specified bus: {{ label("dev.name", self.dev.name) }}
    {% endmacro %}
    """
    _GPIO = TypedDict(
        "_GPIO", {
            "name":
            Annotated[str, Hint("GPIO device name")],
            "driver":
            Annotated[
                str,
                Hint("Name of a GPIO driver class defined in `protoplaster/tests/gpio` "
                     + "(further parameters required)")]
        })
    dev: Annotated[_GPIO, Hint("GPIO device")]
    __GPIO_Pin = TypedDict(
        "__GPIO_Pin", {
            "pin": Annotated[int, Hint("Pin number")],
            "direction": Annotated[str, Hint("Direction ('in' or 'out')")],
            "state": Annotated[bool, Hint("Expected pin state")]
        })
    pins: Annotated[list[__GPIO_Pin], Hint("List of pins to test")]
    test_name: Annotated[str, Hint("Custom name for the test")]

    # backward compatibility with old config format
    number: Annotated[int, Hint("GPIO pin number", hidden=True)]
    value: Annotated[int, Hint("Expected state of pin: 0 or 1", hidden=True)]
    write: Annotated[
        bool,
        Hint("Whether value should be read (false) or written (true)",
             hidden=True)]
    gpio_name: Annotated[
        int | str,
        Hint("Name of GPIO controller: /sys/class/gpio/<name>", hidden=True)]

    def configure(self) -> None:
        if not hasattr(self, "dev"):
            pr_warn(
                "Parameter `dev` missing, falling back to old config format")
            self.dev = {
                "driver":
                "GPIO_sysfs",
                "name":
                "/sys/class/gpio/" +
                getattr(self, "gpio_name", str(self.number)),
                "gpio_names":
                [self.gpio_name] if hasattr(self, "gpio_name") else []
            }  # type: ignore
            self.pins = [
                dict(pin=getattr(self, "number"),
                     direction="out",
                     state=getattr(self, "value"))
            ]
        driver_name = self.dev["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.gpio.{driver_name}.{driver_name}")
        driver = getattr(module, driver_name)
        assert issubclass(
            driver, GPIO), f"Class {driver_name} must implement class GPIO"
        self.nums, self.dirs, self.states = zip(
            *[p.values() for p in self.pins])
        self.gpio = driver(self.nums, self.dirs, **self.dev, export=True)

    def test_is_alive(self) -> None:
        """
        {% macro test_is_alive(self) -%}
          (if applicable) check if device {{ label("dev.name", self.dev.name) }} responds
        {%- endmacro %}
        """
        if not hasattr(self.gpio, "is_alive"):
            pytest.skip(
                "Selected driver doesn't implement the `is_alive` method. No way to check if device responds"
            )
        assert self.gpio.is_alive(), "GPIO device does not respond correctly"

    def test_read_write(self) -> None:
        """
        {% macro test_read_write(self) -%}
          {%- for pin, dir, st in self.pins -%}
            {% if dir == "out" %}
              set pin {{ pin }} to {{ "high" if st else "low" }} and read back to confirm
            {%- else -%}
              confirm pin {{ pin }} is {{ "high" if st else "low" }}
            {% endif %}
          {%- endfor %}
        {%- endmacro %}
        """
        for pin, dir, st in zip(self.nums, self.dirs, self.states):
            if dir == "out":
                self.gpio.set(pin, st)
            st_actual = self.gpio.get(pin)
            assert st == st_actual, f"Read value mismatch on pin {pin}. Expected: {st}, actual: {st_actual}"

    def name(self) -> str:
        return getattr(self, "test_name", None) or self.dev["name"]

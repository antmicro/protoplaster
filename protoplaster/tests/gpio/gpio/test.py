from protoplaster.conf.module import ModuleName
from protoplaster.tests.gpio.PI4IO.PI4IO import PI4IOE5V96224
from protoplaster.tests.gpio.gpio.gpio import GPIO, Direction


@ModuleName("gpio")
class TestGPIO:
    """
    {% macro TestGPIO(prefix) -%}
    GPIOs tests
    -----------
    {% do prefix.append('/sys/class/gpio/gpio') %}
    This module provides tests dedicated to GPIO on specific pin number
    {%- endmacro %}
    """

    def setup_class(self):
        self.gpio_name = self.gpio_name if hasattr(self, "gpio_name") else None

    def test_read_write(self):
        """
        {% macro test_read_write(device) -%}
          - write `{{ device['value'] }}` and read back to confirm (if `write` is enabled, default: no)
          - otherwise, read the input value and confirm it is `{{ device['value'] }}`
        {%- endmacro %}
        """
        if getattr(self, "write", False):
            self._test_write()
        else:
            self._test_read()

    def name(self):
        return f"/sys/class/gpio/{self.number}"

    def _test_read(self):
        with GPIO(self.number, Direction.IN, gpio_name=self.gpio_name) as gpio:
            val = gpio.read_value()
            assert val == self.value, f"Read value mismatch. Expected: {self.value}, Actual: {val}"

    def _test_write(self):
        with GPIO(self.number, Direction.OUT,
                  gpio_name=self.gpio_name) as gpio:
            gpio.write_value(self.value)
            val = gpio.read_value()
            assert val == self.value, (
                f"Incorrect value read back after write. "
                f"Expected: {self.value}, Actual: {val}")

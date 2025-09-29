from protoplaster.conf.module import ModuleName
from protoplaster.gpio.PI4IO.PI4IO import PI4IOE5V96224
from protoplaster.gpio.gpio.gpio import GPIO, Direction


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

    def test_read_write(self):
        """
        {% macro test_read_write(device) -%}
          write `{{ device['value'] }}` and read back to confirm
        {%- endmacro %}
        """
        self.gpio_name = self.gpio_name if hasattr(self, "gpio_name") else None
        with GPIO(self.number, Direction.OUT,
                  gpio_name=self.gpio_name) as gpio:
            gpio.write_value(self.value)
            assert gpio.read_value() == self.value

    def name(self):
        return f"/sys/class/gpio/{self.number}"

from protoplaster.conf.module import ModuleName
from protoplaster.gpio.gpio import GPIO, Direction


@ModuleName("gpio")
class TestGPIO:
    """ GPIOs tests:"""

    def test_read_write(self):
        """
        {% macro test_read_write(gpios) %}
          {% for device in gpios %}
          <li>
            GPIO{{ device['number'] }}: write the value '{{ device['value'] }}' and read to confirm
          </li>
          {% endfor %}
        {% endmacro %}
        """
        with GPIO(self.number, Direction.OUT) as gpio:
            gpio.write_value(self.value)
            assert gpio.read_value() == self.value

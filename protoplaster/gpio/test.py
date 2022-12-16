from protoplaster.conf.module import ModuleName
from protoplaster.gpio.gpio import GPIO, Direction


@ModuleName("gpio")
class TestGPIO:
    """
    GPIOs tests:
    ------------

    This module provides tests dedicated to GPIO on specific pin number:
    """

    def test_read_write(self):
        """
        {% macro test_read_write(device) -%}
          write the value '{{ device['value'] }}' and read to confirm
        {%- endmacro %}
        """
        with GPIO(self.number, Direction.OUT) as gpio:
            gpio.write_value(self.value)
            assert gpio.read_value() == self.value

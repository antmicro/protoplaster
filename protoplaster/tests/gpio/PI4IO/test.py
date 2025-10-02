from protoplaster.conf.module import ModuleName
from protoplaster.tests.gpio.PI4IO.PI4IO import PI4IOE5V96224


@ModuleName("PI4IO")
class TestPI4IO:
    """
    {% macro TestPI4IO(prefix) -%}
    GPIOs tests
    -----------
    This module provides tests dedicated to PI4IO
    {%- endmacro %}
    """

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
        check if PI4IOE5V96224 responds correctly to simple requests
        {%- endmacro %}
        """
        self.gpio = PI4IOE5V96224(self.bus, self.address)
        assert self.gpio.is_alive(), "PI4IOE5V96224 does not respond correctly"

    def name(self):
        return f"PI4IO({self.bus}, {self.address})"

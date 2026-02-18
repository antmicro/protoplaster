from protoplaster.tests.adc.LTC2499.LTC2499 import LTC2499
from protoplaster.conf.module import ModuleName


@ModuleName("LTC2499")
class TestLTC2499:
    """
    {% macro TestLTC2499(prefix) -%}
    LTC2499 device test
    ---------------
    This module provides tests for LTC2499:
    {%- endmacro %}
    """

    def configure(self):
        self.vref = self.vref if hasattr(self, "vref") else 5
        self.adc = LTC2499(self.bus, self.address, self.vref)

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if responds correctly to simple requests
        {%- endmacro %}
        """
        assert self.adc.is_alive(), "LTC2499 does not respond correctly"

    def name(self):
        return f"LTC2499({self.bus}, {self.address})"

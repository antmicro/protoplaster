from protoplaster.conf.module import ModuleName
from protoplaster.tests.dac.LTC2655.LTC2655 import LTC2655


@ModuleName("LTC2655")
class TestLTC2655:
    """
    {% macro TestLTC2655(prefix) -%}
    LTC2655 device test
    ---------------
    This module provides tests for LTC2655:
    {%- endmacro %}
    """

    def setup_class(self):
        self.vref = self.vref if hasattr(self, "vref") else 5
        self.N = self.N if hasattr(self, "N") else 16
        self.adc = LTC2655(self.bus, self.address, self.vref, self.N)

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if LTC2655 responds correctly to simple requests
        {%- endmacro %}
        """
        assert self.adc.is_alive(), "LTC2655 does not respond correctly"

    def name(self):
        return f"LTC2655({self.bus}, {self.address}, {self.vref}, {self.N})"

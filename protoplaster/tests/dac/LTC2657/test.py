import os
from protoplaster.conf.module import ModuleName
from protoplaster.tests.dac.LTC2657.LTC2657 import LTC2657


@ModuleName("LTC2657")
class TestLTC2657:
    """
    {% macro TestLTC2657(prefix) -%}
    LTC2657 device test
    ---------------
    This module provides tests for LTC2657:
    {%- endmacro %}
    """

    def setup_class(self):
        self.vref = self.vref if hasattr(self, "vref") else 5
        self.N = self.N if hasattr(self, "N") else 16
        self.adc = LTC2657(self.bus, self.address, self.vref, self.N)

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if LTC2657 responds correctly to simple requests
        {%- endmacro %}
        """
        assert self.adc.is_alive(), "LTC2657 does not respond correctly"

    def name(self):
        return f"LTC2657({self.bus}, {self.address}, {self.vref}, {self.N})"

from protoplaster.tests.adc.LTC2493.LTC2493 import LTC2493
from protoplaster.conf.module import ModuleName


@ModuleName("LTC2493")
class TestLTC2493:
    """
    {% macro TestLTC2493(prefix) -%}
    LTC2493 device test
    ---------------
    This module provides tests for LTC2493:
    {%- endmacro %}
    """

    def setup_class(self):
        self.vref = self.vref if hasattr(self, "vref") else 5
        self.adc = LTC2493(self.bus, self.address, self.vref)

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if responds correctly to simple requests
        {%- endmacro %}
        """
        assert self.adc.is_alive(
        ), f"LTC2493 does not respond correctly. Reason: {self.adc.fail_reason}"

    def name(self):
        return f"LTC2493({self.bus}, {self.address}, {self.vref})"

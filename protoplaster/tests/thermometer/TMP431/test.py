from protoplaster.conf.module import ModuleName
from protoplaster.tests.thermometer.TMP431.TMP431 import TMP431


@ModuleName("TMP431")
class TestTMP431:
    """
    {% macro TestTMP431(prefix) -%}
    TMP431 device test
    ----------------
    This module provides tests for TMP431:
    {%- endmacro %}
    """

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if TMP431 responds correctly to simple requests
        {%- endmacro %}
        """
        self.smbus_force = getattr(self, "smbus_force", False)
        thermometer = TMP431(self.bus, self.address, self.smbus_force)
        assert thermometer.is_alive(), f"TMP431 does not respond correctly"

    def name(self):
        return f"TMP431({self.bus}, {hex(self.address)})"

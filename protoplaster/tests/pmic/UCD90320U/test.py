from protoplaster.conf.module import ModuleName
from protoplaster.tests.pmic.UCD90320U.UCD90320U import UCD90320U


@ModuleName("UCD90320U")
class TestUCD90320U:
    """
    {% macro TestUCD90320U(prefix) -%}
    UCD90320U device test
    ----------------
    {% do prefix.append('') %}
    This module provides tests for UCD90320U:
    {%- endmacro %}
    """

    def test_is_alive(self):
        """
        {% macro test_is_alive(device) -%}
          check if UCD90320U responds correctly to simple requests
        {%- endmacro %}
        """
        self.smbus_force = getattr(self, "smbus_force", False)
        pmic = UCD90320U(self.bus, self.address, self.smbus_force)
        assert pmic.is_alive(), "UCD90320U does not respond correctly"

    def name(self):
        return f"UCD90320U({self.bus}, {hex(self.address)})"

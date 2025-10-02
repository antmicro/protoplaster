from protoplaster.conf.module import ModuleName
from protoplaster.tests.i2c_mux.TCA9548A.TCA9548A import TCA9548A


@ModuleName("TCA9548A")
class TestTCA9548A:
    """
    {% macro TestDAC(prefix) -%}
    DAC device test
    ---------------
    This module provides tests for DAC devices:
    {%- endmacro %}
    """

    def test_is_alive(self):
        """
        {% macro test_sysfs_interface(device) -%}
        check if TCA9548A responds correctly to simple requests
        {%- endmacro %}
        """
        mux = TCA9548A(self.i2c_bus, self.i2c_address)
        assert mux.is_alive(), "TCA9548A does not respond correctly"

    def name(self):
        return f"TCA9548A({self.i2c_bus}, {self.i2c_address})"

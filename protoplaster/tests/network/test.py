from protoplaster.conf.module import ModuleName
from protoplaster.tests.network.network import NETWORK


@ModuleName("network")
class TestNetwork:
    """
    {% macro TestNetwork(prefix) -%}
    Network interfaces tests
    -------------------
    {% do prefix.append('') %}
    This module provides tests dedicated to network interfaces:
    {%- endmacro %}
    """

    def test_exist(self):
        """
        {% macro test_exist(device) -%}
          check if the interface exist
        {%- endmacro %}
        """
        device = NETWORK(self.interface)
        assert device.check_existence(
        ), f"No interface found: {self.interface}"

    def name(self):
        return self.interface

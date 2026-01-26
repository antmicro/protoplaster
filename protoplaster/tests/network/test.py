import pytest
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

    def test_speed(self):
        """
        {% macro test_speed(device) -%}
          check if the interface speed is {{ device['speed'] }}Mb/s
        {%- endmacro %}
        """
        if not hasattr(self, 'speed'):
            pytest.skip("speed parameter not set")

        device = NETWORK(self.interface)
        current_speed = device.read_speed()

        assert current_speed is not None, f"Could not read speed for {self.interface} (is link down?)"
        assert current_speed == self.speed, f"Expected speed {self.speed}, but got {current_speed}"

    def name(self):
        return self.interface

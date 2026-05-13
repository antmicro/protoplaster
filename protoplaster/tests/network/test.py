import pytest
from protoplaster.conf.module import ModuleName
from protoplaster.tests.network.network import NETWORK
from protoplaster.docs.docs import Hint
from typing import Annotated


@ModuleName("network")
class TestNetwork:
    """
    {% macro TestNetwork(device) -%}
    Network interface tests
    -------------------
    This module provides tests dedicated to network interfaces: {{ label("interface", device['interface']) }}
    {% endmacro %}
    """
    interface: Annotated[
        str, Hint("Network device to perform tests on", required=True)]
    speed: Annotated[str, Hint("Speed of network device [Mbit/s]")]

    def test_exist(self) -> None:
        """
        {% macro test_exist(device) -%}
          check if the interface exists
        {%- endmacro %}
        """
        device = NETWORK(self.interface)
        assert device.check_existence(
        ), f"No interface found: {self.interface}"

    def test_speed(self) -> None:
        """
        {% macro test_speed(device) -%}
          check if the interface speed is {{ label("speed", device['speed']) }} Mbit/s
        {%- endmacro %}
        """
        if not hasattr(self, 'speed'):
            pytest.skip("speed parameter not set")

        device = NETWORK(self.interface)
        current_speed = device.read_speed()

        assert current_speed is not None, f"Could not read speed for {self.interface} (is link down?)"
        assert current_speed == self.speed, f"Expected speed {self.speed}, but got {current_speed}"

    def name(self) -> str:
        return self.interface

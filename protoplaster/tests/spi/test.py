from protoplaster.conf.module import ModuleName
from protoplaster.tests.spi.spi import SPI


@ModuleName("spi")
class TestSPI:
    """
    {% macro TestSPI(prefix) -%}
    SPI device tests
    -----------------
    {% do prefix.append('/dev/spidev') %}
    This module provides tests dedicated to SPI devices:
    {%- endmacro %}
    """

    def configure(self):
        self.spi = SPI(self.bus, self.device)

    def test_loopback(self):
        """
        {% macro test_loopback(device) -%}
          check if an SPI device loops back data transferred to it
        {%- endmacro %}
        """
        data = bytes(range(2**8))
        assert self.spi.transfer(data) == data, "SPI device does not loop back"

    def name(self):
        return f"/dev/spidev{self.bus}.{self.device}"

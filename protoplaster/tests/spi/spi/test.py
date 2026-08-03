from protoplaster.conf.module import ModuleName
from protoplaster.tests.spi.spi.spi import SPI
import importlib
from typing import Annotated, TypedDict
from protoplaster.docs.docs import Hint
from protoplaster.tools.log import pr_warn


@ModuleName("spi")
class TestSPI:
    """
    {% macro TestSPI(self) -%}
    SPI device tests
    -----------------
    This module provides tests dedicated to SPI devices: {{ label("dev.name", self.dev.name) }}
    {% endmacro %}
    """
    __SPI = TypedDict(
        "__SPI", {
            "name":
            Annotated[str, Hint("SPI device name")],
            "driver":
            Annotated[
                str,
                Hint("Name of an SPI driver class defined in " +
                     "`protoplaster/tests/spi` (further parameters required)")]
        })
    dev: Annotated[__SPI, Hint("Device config")]
    command: Annotated[list[int], Hint("Command to send")]
    response_expected: Annotated[list[int],
                                 Hint("Expected response to command")]

    # backward compatibility with old config format
    bus: Annotated[int | str,
                   Hint("Spidev bus: /dev/spidev<bus>.<device>", hidden=True)]
    device: Annotated[
        int | str,
        Hint("Spidev device: /dev/spidev<bus>.<device>", hidden=True)]

    def configure(self) -> None:
        if not hasattr(self, "dev"):
            pr_warn(
                "Parameter `dev` missing, falling back to old config format")
            self.dev = {
                "driver": "SPI_spidev",
                "bus": self.bus,
                "device": self.device,
                "name": f"/dev/spidev{self.bus}.{self.device}"  # type: ignore
            }
        driver_name = self.dev["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.spi.{driver_name}.{driver_name}")
        driver = getattr(module, driver_name)
        assert issubclass(
            driver, SPI), f"Class {driver_name} must implement class 'SPI'"
        self.spi_bus = driver(**self.dev)

    def test_spi_response(self) -> None:
        """
        {% macro test_spi_response(self) -%}
          {% set resp_hex = [] -%}
          {% for b in self.response_expected -%}
            {% do resp_hex.append("%0x" | format(b)) -%}
          {% endfor -%}
          check if device responds to command {{ label("command", self.command and "%x" | format(self.command)) }} with {{ label("response_expected", resp_hex) }}
        {%- endmacro %}
        """
        if hasattr(self, "command"):
            expected = bytes(self.response_expected)
        else:
            self.command = list(range(2**8))
            expected = bytes(self.command)
        response = self.spi_bus.exchange(self.command, len(expected))
        assert response == expected, "SPI response could not be received or is incorrect: (expected: '{expected}', got: '{response}')"

    def name(self):
        return self.dev["name"]

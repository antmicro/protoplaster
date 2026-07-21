from protoplaster.tests.adc.adc.adc import ADC
from protoplaster.conf.module import ModuleName
import importlib
from math import isclose
from pytest import skip
from typing import Annotated, TypedDict
from protoplaster.docs.docs import Hint
from protoplaster.tools.log import pr_warn


@ModuleName("adc")
class TestADC:
    """
    {% macro TestADC(self) -%}
    ADC device test
    ---------------
    This module provides tests for ADC devices: {{ label("dev.name", self.dev.name) }}
    {% endmacro %}
    """
    __ADC = TypedDict(
        "__ADC", {
            "name":
            Annotated[str, Hint("Name of ADC")],
            "driver":
            Annotated[
                str,
                Hint("Name of an ADC driver class defined in " +
                     "`protoplaster/tests/adc` (further parameters required)")]
        })
    dev: Annotated[__ADC, Hint("ADC device config")]
    device_name: Annotated[
        str, Hint("Expected name for drivers that can return a name")]
    tolerance: Annotated[
        float,
        Hint("Absolute tolerance for results measured vs expected [V]")]
    __Channel = TypedDict(
        "__Channel", {
            "channel": Annotated[int, Hint("Channel number")],
            "v_expected": Annotated[float,
                                    Hint("Expected voltage for channel")]
        })
    channels: Annotated[list[__Channel],
                        Hint("Device-dependent channel configuration")]

    # backward compatibility with old config format
    sysfs_path: Annotated[str, Hint("Path to IIO ADC", hidden=True)]
    channel: Annotated[str, Hint("ADC channel", hidden=True)]
    max_voltage: Annotated[str,
                           Hint("Maximum acceptable voltage", hidden=True)]
    min_voltage: Annotated[str,
                           Hint("Minimum acceptable voltage", hidden=True)]

    def configure(self) -> None:
        if not hasattr(self, "dev"):
            pr_warn(
                "Parameter `dev` missing, falling back to old config format")
            path = getattr(self, "sysfs_path",
                           "/sys/bus/iio/devices/iio:device0")
            self.dev = {
                "driver": "ADC_IIO",
                "path": path,
                "name": f"ADC({path})"
            }  # type: ignore
            self.channels = {"channel": self.channel}  # type: ignore
        driver_name = self.dev["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.adc.{driver_name}.{driver_name}")
        model = getattr(module, driver_name)
        assert issubclass(
            model, ADC), f"Class {driver_name} must implement interface ADC"
        self.adc = model(**self.dev)

    def test_is_alive(self) -> None:
        """
        {% macro test_is_alive(self) -%}
          check if {{ label("dev.name", self.dev.name) }} exists and responds
        {%- endmacro %}
        """
        assert self.adc.is_alive(), "ADC does not respond correctly" + (
            (": " +
             self.adc.fail_reason) if hasattr(self.adc, "fail_reason") else "")

    def test_device_name(self) -> None:
        """
        {% macro test_device_name(self) -%}
          (if applicable) check if the device name is {{ label("device_name", self.device_name) }}
        {%- endmacro %}
        """
        if not hasattr(self.adc, "get_device_name"):
            skip("Selected driver does not implement `get_device_name`")
        assert self.adc.get_device_name(
        ) == self.device_name, "The device name is not correct"

    def test_read_adc(self) -> None:
        """
        {% macro test_read_adc(self) -%}
        {%- set tol = ("%g%%" | format((self.tolerance * 100) | float)) if self.tolerance is defined else "0.5 V" -%}
        verify that voltages measure within {{ label("self.tolerance", tol) }} of their expected values
          {%- for channel in self.channels %}
            * channel {{ channel.channel }}: {{ channel.v_expected }} V
          {%- endfor %}
        {%- endmacro %}
        """
        for channel in self.channels:
            raw = self.adc.read_adc(channel["channel"])
            curr_voltage = self.adc.convert_voltage(raw, **channel)
            v_expected = channel["v_expected"]
            tol = getattr(self, "tolerance", 0.5)
            assert isclose(
                curr_voltage, v_expected, abs_tol=tol
            ), f"Voltage of {curr_voltage:.3f} V is not within {tol} V of {v_expected} V"
        # for backward-compatible configs
        if hasattr(self, "channel"):
            raw = self.adc.read_adc(self.channel)
            curr_voltage = self.adc.convert_voltage(raw, self.channel)
            if hasattr(self, "max_voltage"):
                assert curr_voltage <= self.max_voltage, f"Voltage of {curr_voltage:.3f} V is higher than {self.max_voltage} V"
            if hasattr(self, "min_voltage"):
                assert curr_voltage >= self.min_voltage, f"Voltage of {curr_voltage:.3f} V is lower than {self.min_voltage} V"

    def name(self) -> str:
        return self.dev["name"]

from protoplaster.conf.module import ModuleName
from protoplaster.tests.i2c.i2c.i2c import I2C
from protoplaster.tests.i2c.i2c.test import TestI2C
from protoplaster.tests.i2c.i2c_mux.I2CMux import I2CMux
import importlib
from typing import Annotated, TypedDict
from protoplaster.docs.docs import Hint
import pytest


@ModuleName("i2c_mux")
class TestI2CMux:
    """
    {% macro TestI2CMux(self) -%}
    I2C multiplexer test
    ---------------
    This module provides generic tests for I2C multiplexers: {{ label("dev.name", self.dev.name) }}
    {% endmacro %}
    """
    __Mux = TypedDict(
        "__Mux", {
            "name":
            Annotated[str, Hint("Device name")],
            "model":
            Annotated[
                str,
                Hint("Name of a mux driver class defined in `protoplaster/tests/i2c/i2c_mux` "
                     + "(further parameters may be required)")],
            "parent":
            Annotated[TestI2C._I2C,
                      Hint("Parent I2C bus (attribute `dev` of I2C test)")],
            "i2c_address":
            Annotated[int, Hint("I2C address of multiplexer")],
            "reset_gpio":
            Annotated[int | None, Hint("GPIO reset pin")],
            "reset_state":
            Annotated[
                bool,
                Hint("GPIO reset pin logic level -- active-low (False) or active-high (True)"
                     )]
        })

    dev: Annotated[__Mux, Hint("I2C multiplexer")]

    mask_after_reset = b"\x00"

    def configure(self) -> None:
        driver_name = self.dev["parent"]["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.i2c.{driver_name}.{driver_name}")
        driver = getattr(module, driver_name)
        assert issubclass(
            driver, I2C), f"Class {driver_name} must implement class 'I2C'"
        parent = driver(**self.dev["parent"])
        driver_name = self.dev["model"]
        module = importlib.import_module(
            f"protoplaster.tests.i2c.i2c_mux.{driver_name}.{driver_name}")
        driver = getattr(module, driver_name)
        assert issubclass(
            driver,
            I2CMux), f"Class {driver_name} must implement class 'I2CMux'"
        self.mux = driver(parent, self.dev["i2c_address"])

    def test_is_alive(self) -> None:
        """
        {% macro test_is_alive(self) -%}
        check if muxer responds correctly to simple requests
        {%- endmacro %}
        """
        assert self.mux.is_alive(
        ), f"Multiplexer does not respond correctly: {self.mux.fail_reason}"

    def test_reset(self) -> None:
        """
        {% macro test_reset(self) -%}
        {% set rst = (self.dev.reset_gpio is defined) -%}
        {{ "" if rst else "(skipped)" }} check whether the multiplexer responds correctly to a reset triggered by pulling {{ "pin " ~ self.dev.reset_gpio if rst else "the reset pin" }} {{ "high" if self.dev.reset_state else "low" }}
        {%- endmacro %}
        """
        if None in (self.dev.get("reset_gpio"), self.dev.get("reset_state")):
            pytest.skip("Reset pin not configured")
        arbitrary_mask = b"\xA1"
        self.mux.set_mask(arbitrary_mask)
        assert self.mux.reset(), "Could not reset muxer"
        current_mask = self.mux.get_mask()
        assert current_mask == TestI2CMux.mask_after_reset, f"Reset mask mismatch: expected {TestI2CMux.mask_after_reset.hex()}, read {current_mask.hex()}"

    def name(self):
        return self.dev["name"]

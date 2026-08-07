from protoplaster.conf.module import ModuleName
from protoplaster.tests.flash.flash.flash import Flash
from pathlib import Path
import importlib
from typing import Annotated, TypedDict
from protoplaster.docs.docs import Hint


@ModuleName("flash")
class TestFlash:
    """
    {% macro TestFlash(self) -%}
    Flash chip test
    -----------------
    This module provides tests dedicated to flash chips: {{ label("dev.name", self.dev.name) }}
    {% endmacro %}
    """
    __Flash = TypedDict(
        "__Flash", {
            "name":
            Annotated[str, Hint("Storage device name")],
            "driver":
            Annotated[
                str,
                Hint("Name of a device driver class defined in " +
                     "`protoplaster/tests/flash` (further parameters required)"
                     )]
        })
    dev: Annotated[__Flash, Hint("Device config", required=True)]
    binary: Annotated[str, Hint("Path to file to be flashed", required=True)]

    def configure(self) -> None:
        bin_file_path = Path(self.binary)
        assert bin_file_path.exists(
        ), f"Binary file not found at {self.binary}"
        with open(bin_file_path, "rb") as f:
            file_data = f.read()
        assert file_data, f"No data read from {bin_file_path}"
        self.file_data = file_data

        driver_name = self.dev["driver"]
        module = importlib.import_module(
            f"protoplaster.tests.flash.{driver_name}.{driver_name}")
        model = getattr(module, driver_name)
        assert issubclass(
            model, Flash), f"Class {driver_name} must implement class 'Flash'"
        self.device = model(**self.dev)

    def test_presence(self) -> None:
        """
        {% macro test_presence(self) -%}
            check if device {{ label("dev.name", self.dev.name) }} is present
        {%- endmacro %}
        """
        assert self.device.check_presence()

    def test_flashing(self) -> None:
        """
        {% macro test_flashing(self) -%}
            try flashing file {{ label("binary", self.binary) }} onto device
        {%- endmacro %}
        """
        self.device.flash(self.file_data)

    def test_validate_flashing(self) -> None:
        """
        {% macro test_validate_flashing(self) -%}
            check if file was flashed correctly (if possible)
        {%- endmacro %}
        """
        self.device.validate(self.file_data)

    def name(self) -> str:
        return self.dev["name"]

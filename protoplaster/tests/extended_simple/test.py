import pytest

from protoplaster.conf.module import ModuleName
from protoplaster.tests.simple.test import TestSimple
from protoplaster.docs.docs import Hint
from typing import Annotated


@ModuleName("extended_simple")
class TestExtendedSimple(TestSimple):
    """
    {% macro TestExtendedSimple(prefix) -%}
    Extended simple tests
    ---------------
    This module extends TestSimple:
    {%- endmacro %}
    """
    skipped_devices: Annotated[list[str], Hint("List of devices to skip")] = []

    def configure(self):
        super().configure(self)

    def test_conditional_skip(self) -> None:
        """
        {% macro test_conditional_skip(device) -%}
           This test is skipped if the device name is "skip" or its contained in skipped_devices list
        {%- endmacro %}
        """

        if self.device in self.skipped_devices:
            pytest.skip("device is in skipped_devices list")

        super().test_conditional_skip()

    def name(self) -> str:
        return f"extended_simple({self.device})"

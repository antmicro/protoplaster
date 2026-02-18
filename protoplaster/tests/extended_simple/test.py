import pytest

from protoplaster.conf.module import ModuleName
from protoplaster.tests.simple.test import TestSimple


@ModuleName("extended_simple")
class TestExtendedSimple(TestSimple):
    skipped_devices = []
    device = None

    def configure(self):
        assert self.device is not None, "'device' is an obligatory argument"

    def test_conditional_skip(self):
        """
        {% macro test_conditional_skip(device) -%}
           This test is skipped if the device name is "skip" or its contained in skipped_devices list
        {%- endmacro %}
        """

        if self.device in self.skipped_devices:
            pytest.skip("device is in skipped_devices list")

        super().test_conditional_skip()

    def name(self):
        return f"extended_simple({self.device})"

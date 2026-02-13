import pytest

from protoplaster.conf.module import ModuleName
from protoplaster.tests.simple.test import TestSimple


@ModuleName("extended_simple")
class TestExtendedSimple(TestSimple):
    skipped_devices = []
    device = None

    def setup_class(self):
        assert self.device is not None, "'device' is an obligatory argument"

    def test_conditional_skip(self, record_property):
        """
        {% macro test_conditional_skip(device) -%}
           This test is skipped if the device name is "skip" or its contained in skipped_devices list
        {%- endmacro %}
        """

        if self.device in self.skipped_devices:
            pytest.skip("device is in skipped_devices list")

        super().test_conditional_skip(
            record_property=record_property
        )  # 'record_property' is an obligatory kwarg in protoplaster tests if its not an arg

    def name(self):
        return f"extended_simple({self.device})"

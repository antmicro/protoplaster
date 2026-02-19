import pytest
from protoplaster.conf.module import ModuleName
from protoplaster.tests.simple.simple import Simple
import os


@ModuleName("simple")
class TestSimple:
    """
    {% macro TestSimple(prefix) -%}
    Simple tests
    ------------
    {% do prefix.append('') %}
    This module provides simple dummy tests:
    {%- endmacro %}
    """
    counter = 0

    def configure(self):
        self.counter += 1

    def test_success(self):
        """
        {% macro test_success(device) -%}
           This test always succeeds.
        {%- endmacro %}
        """
        assert True

    def test_failure(self):
        """
        {% macro test_failure(device) -%}
           This test always fails.
        {%- endmacro %}
        """
        assert False

    def test_conditional_skip(self):
        """
        {% macro test_conditional_skip(device) -%}
           This test is skipped if the device name is "skip"
        {%- endmacro %}
        """
        if getattr(self, "device", None) == "skip":
            pytest.skip()
        assert True

    def test_record_artifact(self, artifacts_dir, record_artifact):
        """
        {% macro test_record_artifact(device) -%}
           This test always succeeds, and records an artifact.
        {%- endmacro %}
        """
        filename = "file.txt"
        with open(os.path.join(artifacts_dir, filename), 'w') as file:
            file.write("test")
        record_artifact(filename)

        assert True

    def test_configure_runs_once(self):
        """
        Test that asserts `configure` has been executed and the class state
        is correctly initialized for the current test run.
        """
        assert type(
            self
        ).counter == 1, f"configure was run {type(self).counter} times!"

    def name(self):
        return "simple" + (f"({self.device})"
                           if hasattr(self, "device") else "")

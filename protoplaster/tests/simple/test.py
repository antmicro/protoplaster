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

    def name(self):
        return "simple"

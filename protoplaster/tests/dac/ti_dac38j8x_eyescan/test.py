import os
import shutil

from protoplaster.conf.module import ModuleName
from .process_eyescan import EyeScan


@ModuleName("ti_dac38j8x_eyescan")
class TestTiDac38j8xEyescan:
    """
    {% macro TestEyeScan(prefix) -%}
    Eye Scan tests
    -----------------
    This module provides tests for Eye Scan:
    {%- endmacro %}
    """

    def setup_class(self):
        assert hasattr(self,
                       "ftdi_dev"), "`ftdi_dev` test attribute is required"
        assert hasattr(self, "bit"), "`bit` test attribute is required"
        assert hasattr(
            self,
            "eyescan_output"), "`eyescan_output` test attribute is required"
        assert hasattr(
            self,
            "eyescan_diagram"), "`eyescan_diagram` test attribute is required"
        assert hasattr(
            self,
            "eyescan_output"), "`eyescan_output` test attribute is required"

        self.eyescan = EyeScan(self.ftdi_dev, self.bit)

    def test_create_diagram(self, record_artifact, artifacts_dir):
        """
        {% macro test_create_diagram(device) -%}
          parse `{{ device['data'] }}` and create diagram
          {% if device['eyescan_diagram'] is defined -%}
            to `{{ device['eyescan_diagram'] }}` file
          {%- endif %}
        {%- endmacro %}
        """
        eyescan_output_path = os.path.join(artifacts_dir, self.eyescan_output)
        shutil.copyfile(self.eyescan.get_eyescan_file_path(),
                        eyescan_output_path)
        record_artifact(eyescan_output_path)

        diagram = self.eyescan.render_diagram()

        eyescan_diagram_path = os.path.join(artifacts_dir,
                                            self.eyescan_diagram)
        with open(eyescan_diagram_path, "w") as file:
            file.write(diagram)

        record_artifact(self.eyescan_diagram)

    def test_eye_size(self):
        """
        {% macro test_eye_size(device) -%}
          parse `{{ device['data'] }}` and assert eye size
          {% macro _item(value) -%}
            {%- if device[value] is defined %}
            * `{{ value }}`: {{ device[value] }}
            {%- endif -%}
          {%- endmacro -%}
          {{ _item('min_width') }}
          {{ _item('max_width') }}
          {{ _item('min_height') }}
          {{ _item('max_height') }}
        {%- endmacro %}
        """
        samples = self.eyescan.parse_file()
        samples = self.eyescan.aggregate_samples(samples,
                                                 lambda x: sum(x) / len(x))

        min_width = getattr(self, "min_width", -float('inf'))
        max_width = getattr(self, "max_width", float('inf'))
        min_height = getattr(self, "min_height", -float('inf'))
        max_height = getattr(self, "max_height", float('inf'))

        assert min_width <= max_width, f"Invalid range: [{min_width}, {max_width}]"
        assert min_height <= max_height, f"Invalid range: [{min_height}, {max_height}]"

        for sample in samples:
            width, height = self.eyescan.get_eye_size(sample)
            assert min_width <= width <= max_width, f"Eye width {width} is not in accepted range: [{min_width}, {max_width}]"
            assert min_height <= height <= max_height, f"Eye height {height} is not in accepted range: [{min_height}, {max_height}]"

    def name(self):
        return "eyescan"

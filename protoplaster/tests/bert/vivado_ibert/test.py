import os
import shutil

from protoplaster.conf.module import ModuleName
from .ibert_eyescan import EyeScan


@ModuleName("vivado_ibert")
class TestIbertEyescan:
    """
    {% macro TestIbertEyescan(prefix) -%}
    Eye Scan tests
    -----------------
    This module provides tests for Eye Scan using IBERT:
    {%- endmacro %}
    """

    def setup_class(self):
        assert hasattr(
            self,
            "serial_number"), "`serial_number` test attribute is required"
        assert hasattr(
            self, "channel_path"), "`channel_path` test attribute is required"
        assert getattr(self, "prbs_bits", None) in self._BERT_PRBS_BITS, (
            "`prbs_bits` test attribute is required "
            f"and must be one of {self._BERT_PRBS_BITS}")
        assert hasattr(
            self,
            "eyescan_output"), "`eyescan_output` test attribute is required"
        assert hasattr(
            self,
            "eyescan_diagram"), "`eyescan_diagram` test attribute is required"

        vivado_cmd = getattr(self, "vivado_cmd", "vivado")
        hw_server = getattr(self, "hw_server", "localhost:3121")
        if not hasattr(self, "test_name"):
            self.test_name = (
                f"vivado_ibert eyescan: {self.prbs_bits}-bit PRBS "
                f"on {hw_server}/{self.serial_number}/{self.channel_path}")
        self.eyescan = EyeScan(vivado_cmd, hw_server, self.serial_number,
                               self.channel_path, self.prbs_bits)

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
        return self.test_name

    _BERT_PRBS_BITS = {7, 15, 23, 31}

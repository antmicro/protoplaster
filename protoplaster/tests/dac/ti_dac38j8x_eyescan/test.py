import os
import shutil

from protoplaster.conf.module import ModuleName
from .process_eyescan import EyeScan
from eyescan.instructions import TestPattern


@ModuleName("ti_dac38j8x_eyescan")
class TestTiDac38j8xEyescan:
    """
    {% macro TestEyeScan(prefix) -%}
    Eye Scan tests
    -----------------
    This module provides tests for Eye Scan:
    {%- endmacro %}
    """

    def configure(self):
        assert hasattr(self, "bit"), "`bit` test attribute is required"
        assert hasattr(
            self,
            "eyescan_output"), "`eyescan_output` test attribute is required"
        assert hasattr(
            self,
            "eyescan_diagram"), "`eyescan_diagram` test attribute is required"
        assert hasattr(
            self, "sample_rate"), "`sample_rate` test attribute is required"
        assert hasattr(self,
                       "dwell_time"), "`dwell_time` test attribute is required"

        def parse_test_pattern(pattern):
            try:
                return TestPattern[pattern]
            except KeyError:
                raise ValueError(
                    f"{pattern} is not a valid test pattern ({[str(i) for i in TestPattern]})"
                )

        if not hasattr(self, "ftdi_jtag_frequency"):
            setattr(self, "ftdi_jtag_frequency", 1E5)
        if not hasattr(self, "ftdi_direction"):
            setattr(self, "ftdi_direction", 0x308B)
        if not hasattr(self, "ftdi_initial_value"):
            setattr(self, "ftdi_initial_value", 0x2088)
        if not hasattr(self, "ftdi_reset_bit"):
            setattr(self, "ftdi_reset_bit", 0x2000)
        if not hasattr(self, "daisy_chain_count"):
            setattr(self, "daisy_chain_count", 1)
        if not hasattr(self, "daisy_chain_number"):
            setattr(self, "daisy_chain_number", 1)
        if not hasattr(self, "pyftdi_url"):
            setattr(self, "pyftdi_url", "ftdi:///1")
        if not hasattr(self, "test_pattern"):
            setattr(self, "test_pattern", TestPattern.PRBS_7_BIT)
        else:
            self.test_pattern = parse_test_pattern(self.test_pattern)
        if not hasattr(self, "voltage_increment"):
            setattr(self, "voltage_increment", 1)
        if not hasattr(self, "phase_increment"):
            setattr(self, "phase_increment", 1)

        self.eyescan = EyeScan(
            pyftdi_url=self.pyftdi_url,
            ftdi_jtag_frequency=self.ftdi_jtag_frequency,
            ftdi_direction=self.ftdi_direction,
            ftdi_initial_value=self.ftdi_initial_value,
            ftdi_reset_bit=self.ftdi_reset_bit,
            daisy_chain_device_number=self.daisy_chain_number,
            daisy_chain_device_count=self.daisy_chain_count,
            bit=self.bit,
            test_pattern=self.test_pattern,
            sample_rate=self.sample_rate,
            dwell_time=self.dwell_time,
            voltage_increment=self.voltage_increment,
            phase_increment=self.phase_increment)

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
        return "eyescan-" + str(self.daisy_chain_number)

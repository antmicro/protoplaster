from collections import defaultdict
import csv
import os
import tempfile
from typing import Callable

from jinja2 import Environment, DictLoader
from eyescan.eyescan import perform_eyescan
from eyescan.instructions import TestPattern


class EyeScan:

    def __init__(self, pyftdi_url: str, ftdi_jtag_frequency: float,
                 ftdi_direction: int, ftdi_initial_value: int,
                 ftdi_reset_bit: int, daisy_chain_device_number: int,
                 daisy_chain_device_count: int, bit: int,
                 test_pattern: TestPattern, sample_rate: int,
                 dwell_time: float, voltage_increment: int,
                 phase_increment: int) -> None:
        self.eyescan_file = tempfile.NamedTemporaryFile()
        self.axis_multiplier = {"x": 1, "y": 10}
        self.bit = bit
        self.sample_rate = sample_rate
        self.dwell_time = dwell_time
        self.voltage_increment = voltage_increment
        self.phase_increment = phase_increment

        perform_eyescan(pyftdi_url=pyftdi_url,
                        ftdi_jtag_frequency=ftdi_jtag_frequency,
                        ftdi_direction=ftdi_direction,
                        ftdi_initial_value=ftdi_initial_value,
                        ftdi_reset_bit=ftdi_reset_bit,
                        daisy_chain_device_number=daisy_chain_device_number,
                        daisy_chain_device_count=daisy_chain_device_count,
                        output_path=self.eyescan_file.name,
                        bit_number=bit,
                        test_pattern=test_pattern,
                        dwell_time=dwell_time,
                        voltage_increment=voltage_increment,
                        phase_increment=phase_increment)

    def fill_increment_data(self, samples_by_lane):
        for samples in samples_by_lane:
            for voltage in range(31, -33, -1):
                for phase in range(15, -17, -1):
                    if voltage not in range(
                            31, -33, -1 * self.voltage_increment) and (
                                voltage + 1,
                                phase) in samples_by_lane[samples]:
                        samples_by_lane[samples][(
                            voltage,
                            phase)] = samples_by_lane[samples][(voltage + 1,
                                                                phase)]
                    if phase not in range(
                            15, -17, -1 * self.phase_increment) and (
                                voltage,
                                phase + 1) in samples_by_lane[samples]:
                        samples_by_lane[samples][(
                            voltage,
                            phase)] = samples_by_lane[samples][(voltage,
                                                                phase + 1)]
        return samples_by_lane

    def parse_file(self) -> list[dict]:
        samples_by_lane = defaultdict(lambda: defaultdict(list))
        with open(self.eyescan_file.name) as file:
            for row in csv.reader(file, delimiter="\t"):
                lane, bit, y, x, amp = map(int, row)
                samples_by_lane[lane][(y, x)].append((bit, amp))
        samples_by_lane = self.fill_increment_data(samples_by_lane)
        return [lane for _, lane in sorted(samples_by_lane.items())]

    def aggregate_samples(self,
                          samples: list[dict],
                          agg_lane_bits: Callable = lambda x: x) -> list[list]:
        return [[{
            "y": k[0],
            "x": k[1],
            "amp": agg_lane_bits([i[1] for i in sorted(lane[k])])
        } for k in lane] for lane in samples]

    def read_diagram_template(self) -> str:
        with open(f"{os.path.dirname(__file__)}/eye_diagram.html") as file:
            return file.read()

    def read_base_template(self) -> str:
        with open(
                f"{os.path.dirname(__file__)}/../../../webui/templates/base.html"
        ) as file:
            return file.read()

    def render_template(self, html_template: str, **kwargs) -> str:
        base_template = self.read_base_template()

        environment = Environment(loader=DictLoader({
            "template": html_template,
            "base.html": base_template
        }))
        template = environment.get_template("template")
        return template.render(**kwargs)

    def render_diagram(self) -> str:
        samples = self.parse_file()
        samples = self.aggregate_samples(samples)
        diagram_template = self.read_diagram_template()
        return self.render_template(diagram_template,
                                    samples=samples,
                                    axis_multiplier=self.axis_multiplier,
                                    disable_nav=True,
                                    num_bits=self.bit,
                                    sample_number=self.dwell_time *
                                    self.sample_rate)

    def get_eyescan_file_path(self) -> str:
        return self.eyescan_file.name

    def get_eye_size(self, sample: list[dict]) -> tuple[int, int]:
        max_value = max(pixel["amp"] for pixel in sample)
        eye_pixels = [pixel for pixel in sample if pixel["amp"] != max_value]
        x_values = [pixel["x"] for pixel in eye_pixels]
        y_values = [pixel["y"] for pixel in eye_pixels]
        if len(x_values):
            width = max(x_values) - min(x_values)
        else:
            width = 0
        if len(y_values):
            height = max(y_values) - min(y_values)
        else:
            height = 0
        return (width * self.axis_multiplier["x"],
                height * self.axis_multiplier["y"])

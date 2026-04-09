from collections import defaultdict
import csv
import os
import tempfile
from typing import Callable

from jinja2 import Environment, DictLoader
from eyescan.eyescan import perform_eyescan, perform_parallel_eyescan
from eyescan.instructions import TestPattern


class EyeScan:

    def __init__(self, pyftdi_url: str, ftdi_jtag_frequency: float,
                 ftdi_direction: int, ftdi_initial_value: int,
                 ftdi_reset_bit: int, daisy_chain_device_number: int,
                 daisy_chain_device_count: int, bit: int,
                 test_pattern: TestPattern, sample_rate: int,
                 dwell_time: float, voltage_increment: int,
                 phase_increment: int, parallel: bool) -> None:
        self.eyescan_file = tempfile.NamedTemporaryFile()
        self.axis_multiplier = {"x": 1, "y": 10}
        self.bit = bit
        self.sample_rate = sample_rate
        self.dwell_time = dwell_time
        self.voltage_increment = voltage_increment
        self.phase_increment = phase_increment

        perform_eyescan_func = perform_parallel_eyescan if parallel else perform_eyescan

        perform_eyescan_func(
            pyftdi_url=pyftdi_url,
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
                    if voltage not in range(31, -33,
                                            -1 * self.voltage_increment) and (
                                                voltage + 1, phase) in samples:
                        samples[(voltage, phase)] = samples[(voltage + 1,
                                                             phase)]
                    if phase not in range(15, -17,
                                          -1 * self.phase_increment) and (
                                              voltage, phase + 1) in samples:
                        samples[(voltage, phase)] = samples[(voltage,
                                                             phase + 1)]
        return samples_by_lane

    def parse_file(self) -> dict:
        # samples_by_dac[dac_id][lane_id][(y, x)] = [(bit, amp), ...]
        samples_by_dac = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list)))
        with open(self.eyescan_file.name) as file:
            for row in csv.reader(file, delimiter="\t"):
                dac, lane, bit, y, x, amp = map(int, row)
                samples_by_dac[dac][lane][(y, x)].append((bit, amp))

        sorted_data = {}
        for dac_id in sorted(samples_by_dac.keys()):
            sorted_data[dac_id] = [
                lane for _, lane in sorted(samples_by_dac[dac_id].items())
            ]
            sorted_data[dac_id] = self.fill_increment_data(sorted_data[dac_id])
        return sorted_data

    def aggregate_samples(self,
                          samples_dict: dict,
                          agg_lane_bits: Callable = lambda x: x) -> dict:
        aggregated_data = {}
        for dac_id, lanes in samples_dict.items():
            aggregated_data[dac_id] = [[{
                "y":
                k[0],
                "x":
                k[1],
                "amp":
                agg_lane_bits([i[1] for i in sorted(lane[k])])
            } for k in lane] for lane in lanes]
        return aggregated_data

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
        eyesizes = dict()
        for dac_id, lanes in samples.items():
            eyesizes[dac_id] = dict()
            for i, sample in enumerate(lanes):
                eyesizes[dac_id][i] = dict()
                result = self.get_eye_sizes(sample)
                for bit, val in enumerate(result):
                    eyesizes[dac_id][i][bit] = {
                        "width": val[0],
                        "height": val[1]
                    }
        return self.render_template(diagram_template,
                                    samples=samples,
                                    axis_multiplier=self.axis_multiplier,
                                    disable_nav=True,
                                    num_bits=self.bit,
                                    sample_number=self.dwell_time *
                                    self.sample_rate,
                                    eyesizes=eyesizes)

    def get_eyescan_file_path(self) -> str:
        return self.eyescan_file.name

    def get_eye_size(self, eye_pixels: list) -> tuple[int, int]:
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

    def get_eye_sizes(self, sample: list[dict]) -> list[tuple[int, int]]:
        result = list()
        # Average over all bits
        eye_pixels = [pixel for pixel in sample if sum(pixel["amp"]) == 0]
        result.append(self.get_eye_size(eye_pixels))
        bits = len(sample[0]["amp"]) if len(sample) else 0
        for bit in range(bits):
            eye_pixels = [pixel for pixel in sample if pixel["amp"][bit] == 0]
            result.append(self.get_eye_size(eye_pixels))
        return result

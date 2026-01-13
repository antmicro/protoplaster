from collections import defaultdict
import csv
import os
import tempfile
from typing import Callable

from jinja2 import Environment, DictLoader

TI_DAC38J8X_EYESCAN_LIBRARY = False
try:
    from eyescan.eyescan import perform_eyescan
    TI_DAC38J8X_EYESCAN_LIBRARY = True
except OSError:
    print(
        "Warning: TI DAC38J8X eyescan library is not available. Disabling eyescan module tests."
    )


class EyeScan:

    def __init__(self, ftdi_dev: int, bit: int) -> None:
        self.eyescan_file = tempfile.NamedTemporaryFile()
        self.axis_multiplier = {"x": 1, "y": 10}

        # Check if the eyescan library is available
        assert TI_DAC38J8X_EYESCAN_LIBRARY, "TI DAC38J8X eyescan library is not available."

        perform_eyescan(ftdi_dev, self.eyescan_file.name, bit)

    def parse_file(self) -> list[dict]:
        samples_by_lane = defaultdict(lambda: defaultdict(list))
        with open(self.data_path.name) as file:
            for row in csv.reader(file, delimiter="\t"):
                lane, bit, y, x, amp = map(int, row)
                samples_by_lane[lane][(y, x)].append((bit, amp))
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

    def render_template(self, html_template: str, **kwargs) -> str:
        environment = Environment(
            loader=DictLoader({"template": html_template}))
        template = environment.get_template("template")
        return template.render(**kwargs)

    def render_diagram(self) -> str:
        samples = self.parse_file()
        samples = self.aggregate_samples(samples)
        diagram_template = self.read_diagram_template()
        return self.render_template(diagram_template,
                                    samples=samples,
                                    axis_multiplier=self.axis_multiplier)

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

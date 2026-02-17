import csv
import os
import shutil
import tempfile
import subprocess

from jinja2 import DictLoader, Environment


class EyeScan:

    def __init__(self, vivado_cmd: str, hw_server: str, serial_number: str,
                 channel_path: str, prbs_bits: int, loopback: bool) -> None:
        self.eyescan_file = tempfile.NamedTemporaryFile()
        self.hw_server = hw_server
        self.serial_number = serial_number
        self.channel_path = channel_path
        self.prbs_bits = prbs_bits
        self.loopback = loopback

        # Check if Vivado is available
        if shutil.which(vivado_cmd) is None:
            raise RuntimeError(
                f"{vivado_cmd} not found on PATH, or specified absolute path does not exist"
            )

        # Perform the eye scan
        vivado_argv = [
            vivado_cmd,
            "-mode",
            "batch",
            "-nolog",
            "-nojournal",
            "-source",
            "ibert_eyescan.tcl",
            "-tclargs",
            self.eyescan_file.name,
            self.hw_server,
            self.serial_number,
            self.channel_path,
            str(self.prbs_bits),
            int(self.loopback),
        ]
        res = subprocess.run(vivado_argv,
                             cwd=os.path.dirname(__file__),
                             capture_output=True,
                             text=True)
        if res.returncode != 0:
            raise RuntimeError("Eye scan failed, Vivado stdout:\n" +
                               res.stdout + "\nVivado stderr:\n" + res.stderr)

    def parse_file(self) -> list[dict]:
        samples = []
        with open(self.get_eyescan_file_path()) as file:
            for line in file:
                if line.strip() == "Scan Start":
                    break
            else:
                raise ValueError(
                    "Scan data start marker not found in CSV file")

            reader = csv.reader(file)
            xs = [int(x) for x in next(reader)[1:]]
            for row in reader:
                if row == ["Scan End"]:
                    break
                y, *amps = int(row[0]), *map(float, row[1:])
                for x, amp in zip(xs, amps, strict=True):
                    samples.append({"x": x, "y": y, "amp": amp})
            else:
                raise ValueError("Scan data end marker not found in CSV file")

        return samples

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
            "base.html": base_template,
        }))
        template = environment.get_template("template")
        return template.render(**kwargs)

    def render_diagram(self) -> str:
        samples = self.parse_file()
        diagram_template = self.read_diagram_template()
        return self.render_template(diagram_template,
                                    samples=samples,
                                    disable_nav=True,
                                    num_bits=self.prbs_bits)

    def get_eyescan_file_path(self) -> str:
        return self.eyescan_file.name

    def get_eye_size(self, sample: list[dict]) -> tuple[int, int]:
        min_value = min(pixel["amp"] for pixel in sample)
        eye_pixels = [pixel for pixel in sample if pixel["amp"] != min_value]
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
        return (width, height)

import csv
import os
import shutil
import tempfile
import subprocess
from typing import Literal, Optional

from jinja2 import DictLoader, Environment


class EyeScan:

    def __init__(self, vivado_cmd: str, hw_server: str, serial_number: str,
                 channel_path: str, prbs_bits: int, loopback: bool,
                 dwell_mode: Optional[Literal["BER", "TIME"]],
                 dwell_value: Optional[float],
                 horizontal_increment: Optional[int],
                 vertical_increment: Optional[int]):
        self.eyescan_file = tempfile.NamedTemporaryFile(suffix=".csv")
        self.hw_server = hw_server
        self.serial_number = serial_number
        self.channel_path = channel_path
        self.prbs_bits = prbs_bits
        self.loopback = loopback
        self.report_file = tempfile.NamedTemporaryFile(suffix=".report")
        self.dwell_mode = dwell_mode
        self.dwell_value = dwell_value
        self.horizontal_increment = horizontal_increment
        self.vertical_increment = vertical_increment

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
            str(self.loopback),
            self.report_file.name,
            self.dwell_mode or "",
            str(self.dwell_value) if self.dwell_value is not None else "",
            str(self.horizontal_increment),
            str(self.vertical_increment),
        ]
        res = subprocess.run(vivado_argv,
                             cwd=os.path.dirname(__file__),
                             capture_output=True,
                             text=True)
        if res.returncode != 0:
            raise RuntimeError("Eye scan failed, Vivado stdout:\n" +
                               res.stdout + "\nVivado stderr:\n" + res.stderr)

    def parse_file(self) -> tuple[list[dict], int, int]:
        samples = []
        width = 0
        height = 0
        with open(self.get_eyescan_file_path()) as file:
            for line in file:
                if "Horizontal Opening" in line:
                    width = int(line.split(",")[1])
                elif "Vertical Opening" in line:
                    height = int(line.split(",")[1])
                elif line.strip() == "Scan Start":
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

        return (samples, width, height)

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
        samples, width, height = self.parse_file()
        diagram_template = self.read_diagram_template()
        return self.render_template(diagram_template,
                                    samples=samples,
                                    disable_nav=True,
                                    num_bits=self.prbs_bits,
                                    eye_width=width,
                                    eye_height=height)

    def get_eyescan_file_path(self) -> str:
        return self.eyescan_file.name

    def get_report_file_path(self) -> str:
        return self.report_file.name

    def read_report_file(self) -> str:
        with open(self.report_file.name) as report_file:
            return report_file.read()

    def get_entry_from_report(self, entry) -> str | None:
        with open(self.report_file.name, "r") as report_file:
            for report_line in report_file:
                found_line_splitted = report_line.strip().split(f"{entry}=")
                if len(found_line_splitted) == 2:
                    _, entry_value = found_line_splitted
                    return entry_value
        return None

    def get_transceiver_status(self) -> str | None:
        return self.get_entry_from_report("TRANSCEIVER_STATUS")

    def get_line_rate(self) -> str | None:
        return self.get_entry_from_report("LINE_RATE")

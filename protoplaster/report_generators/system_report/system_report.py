import subprocess
import argparse
import zipfile
from dataclasses import dataclass
import yaml
import os
import sys
import shutil
from jinja2 import Environment, DictLoader


class SummaryConfig:

    def __init__(self, config):
        if "name" in config and "run" in config:
            self.name = config["name"]
            self.script = config["run"]
        else:
            print("Error: summary config is incomplete")
            sys.exit(1)


class CommandConfig:

    def __init__(self, yaml_config):
        name, config = yaml_config
        required_fields_present = "run" in config and "output" in config
        superuser_correct = "superuser" not in config or config[
            "superuser"] in ["required", "preferred"]
        if not required_fields_present or not superuser_correct:
            print(f"Error: {name} config is invalid")
            sys.exit(1)
        self.name = name
        self.script = config["run"]
        if "superuser" in config and not is_root():
            if config["superuser"] == "required":
                print(
                    f"Error: You have insufficient permissions to run {self.script}. No report will be generated."
                )
                sys.exit(1)
            else:
                print(
                    f"Warning: You have insufficient permissions to run {self.script}. Output from this command will be skipped in the report."
                )
        self.summary_configs = [
            SummaryConfig(c) for c in config.get("summary", [])
        ]
        self.output_file = config["output"]


@dataclass
class SubReportSummary:
    title: str
    content: str


@dataclass
class SubReportResult:
    name: str
    raw_output: str
    output_file: str
    summaries: list[SubReportSummary]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o",
                        "--output-file",
                        type=str,
                        help="Path to the output file",
                        default="report.zip")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to the yaml config file",
        default=f"{os.path.dirname(__file__)}/default_commands.yml")
    return parser.parse_args()


def generate_html(sub_reports):
    with open(f"{os.path.dirname(__file__)}/report_template.html"
              ) as template_file:
        html_template = template_file.read()
    environment = Environment(
        loader=DictLoader({"report_template": html_template}))
    template = environment.get_template("report_template")
    return template.render(sub_reports=sub_reports)


def read_config(filename):
    with open(filename) as file:
        return yaml.safe_load(file)


def command_path(command):
    cmd = command.split(" ")
    if shutil.which(cmd[0]):
        return command
    builtin = f"{os.path.dirname(__file__)}/{cmd[0]}"
    if shutil.which(builtin):
        return builtin + " ".join(cmd[1:])
    return None


def read_commands(filename):
    command_configs = []
    for config in read_config(filename).items():
        command_configs.append(CommandConfig(config))
    return command_configs


def get_cmd_output(cmd):
    return subprocess.check_output(cmd,
                                   shell=True,
                                   text=True,
                                   stderr=subprocess.STDOUT)


def is_root():
    return int(get_cmd_output("id -u")) == 0


def main():
    args = parse_args()

    command_configs = read_commands(args.config)

    with open(args.output_file, "wb") as archive_file:
        with zipfile.ZipFile(archive_file, 'w',
                             zipfile.ZIP_DEFLATED) as archive:
            sub_reports = []
            for config in command_configs:
                try:
                    out = get_cmd_output(f"sh -c '{config.script}'")
                    archive.writestr(config.output_file, out)
                    summaries = []
                    for summary_config in config.summary_configs:
                        summary_content = subprocess.check_output(
                            f"sh -c '{summary_config.script}'",
                            shell=True,
                            text=True,
                            stderr=subprocess.STDOUT,
                            env=os.environ | {
                                "PROTOPLASTER_SCRIPTS":
                                f"{os.path.dirname(__file__)}/scripts"
                            },
                            input=out)
                        summaries.append(
                            SubReportSummary(summary_config.name,
                                             summary_content))
                    sub_reports.append(
                        SubReportResult(config.name, out, config.output_file,
                                        summaries))
                except subprocess.CalledProcessError as e:
                    print(
                        f"command {config.name} exited with non-zero return code {e.returncode}"
                    )
            archive.writestr("summary.html", generate_html(sub_reports))
            with open("summary.html", "w") as ofile:
                ofile.write(generate_html(sub_reports))


if __name__ == "__main__":
    main()

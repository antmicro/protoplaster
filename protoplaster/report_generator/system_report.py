import subprocess
import argparse
import zipfile
from dataclasses import dataclass
import yaml
import os
import sys


@dataclass
class Command:
    command: str
    run_as_root: bool
    output_file: str


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


def read_config(filename):
    with open(filename) as file:
        return yaml.safe_load(file)


def is_config_valid(config):
    required_fields_present = "command" in config and "output" in config
    superuser_correct = "superuser" not in config or config["superuser"] in [
        "required", "preferred"
    ]
    return required_fields_present and superuser_correct


def read_commands(filename):
    commands = []
    for name, config in read_config(filename).items():
        if not is_config_valid(config):
            print(f"Error: {name} config is invalid")
            sys.exit(1)
        command = config["command"]
        run_as_root = "superuser" in config
        if run_as_root and not is_root():
            if config["superuser"] == "required":
                print(
                    f"Error: You have insufficient permissions to run {command}. No report will be generated."
                )
                sys.exit(1)
            else:
                print(
                    f"Warning: You have insufficient permissions to run {command}. Output from this command will be skipped in the report."
                )
        else:
            commands.append(Command(command, run_as_root, config["output"]))
    return commands


def get_cmd_output(cmd):
    return subprocess.check_output(cmd,
                                   shell=True,
                                   text=True,
                                   stderr=subprocess.STDOUT)


def is_root():
    return int(get_cmd_output("id -u")) == 0


def is_root():
    return int(get_cmd_output("id -u")) == int(get_cmd_output("id -u root"))


def main():
    args = parse_args()

    commands = read_commands(args.config)

    with open(args.output_file, "wb") as archive_file:
        with zipfile.ZipFile(archive_file, 'w',
                             zipfile.ZIP_DEFLATED) as archive:
            for cmd in commands:
                try:
                    out = get_cmd_output(cmd.command)
                    archive.writestr(cmd.output_file, out)
                except subprocess.CalledProcessError as e:
                    print(f"command {cmd.command} exited with non-zero return code {e.returncode}")

if __name__ == "__main__":
    main()

import subprocess
import argparse
import zipfile
from dataclasses import dataclass


@dataclass
class Command:
    command: str
    output_file: str


commands = [
    Command("uname -a", "uname.txt"),
    Command("sudo dmesg", "dmesg.txt"),
    Command("sudo journalctl", "journalctl.txt"),
    Command("systemctl list-units --all", "systemctl.txt"),
    Command("ip a", "ip.txt"),
    Command("ps -eF", "ps.txt"),
    Command("udevadm info -e", "udevadm.txt")
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o",
                        "--output-file",
                        type=str,
                        help="Path to the output file",
                        default="report.zip")
    return parser.parse_args()


def get_cmd_output(cmd):
    return subprocess.check_output(cmd, shell=True, text=True)


def main():
    args = parse_args()

    with open(args.output_file, "wb") as archive_file:
        with zipfile.ZipFile(archive_file, 'w',
                             zipfile.ZIP_DEFLATED) as archive:
            for cmd in commands:
                out = get_cmd_output(cmd.command)
                archive.writestr(cmd.output_file, out)


if __name__ == "__main__":
    main()

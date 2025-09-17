#!/usr/bin/env python3
import argparse
import os
import sys
from colorama import init, Fore, Style
from flask import Flask
import shutil

import protoplaster.api.v1
from protoplaster.runner.manager import RunManager
from protoplaster.runner.runner import run_tests, list_groups
from protoplaster.report_generators.system_report.protoplaster_system_report import __file__ as system_report_file

CONFIG_DIR = "/etc/protoplaster"
REPORTS_DIR = "/var/lib/protoplaster/reports"
ARTIFACTS_DIR = "/var/lib/protoplaster/artifacts"


def create_docs_app() -> Flask:
    """Create an app that can be used for building the docs

    This only registers the available API routes, this cannot be used to run
    the server! Used for dynamically building the API reference chapter in
    the documentation.
    """
    app = Flask(__name__)
    app.register_blueprint(protoplaster.api.v1.create_routes())
    return app


init()


def warning(text):
    return Fore.YELLOW + f"[WARNING] {text}" + Style.RESET_ALL


def error(text):
    return Fore.RED + f"[ERROR] {text}" + Style.RESET_ALL


def info(text):
    return f"[INFO] {text}"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d",
                        "--test-dir",
                        type=str,
                        default=f"{CONFIG_DIR}",
                        help="Path to the test directory")
    parser.add_argument("-r",
                        "--reports-dir",
                        type=str,
                        default=f"{REPORTS_DIR}",
                        help="Path to the reports directory")
    parser.add_argument("-a",
                        "--artifacts-dir",
                        type=str,
                        default=f"{ARTIFACTS_DIR}",
                        help="Path to the test artifacts directory")
    parser.add_argument(
        "-t",
        "--test-file",
        type=str,
        default=f"test.yaml",
        help="Path to the yaml test description in the test directory")
    parser.add_argument("-g", "--group", type=str, help="Group to execute")
    parser.add_argument("--list-groups",
                        action="store_true",
                        help="List possible groups to execute")
    parser.add_argument("-o",
                        "--output",
                        type=str,
                        help="A junit-xml style report of the tests results")
    parser.add_argument("--csv",
                        type=str,
                        help="Generate a CSV report of the tests results")
    parser.add_argument(
        "--csv-columns",
        type=str,
        help="Comma-separated list of columns to be included in generated CSV")
    parser.add_argument("--generate-docs",
                        action="store_true",
                        help="Generate documentation")
    parser.add_argument("-c",
                        "--custom-tests",
                        type=str,
                        default=f"{CONFIG_DIR}/tests/*/",
                        help="Path to the custom tests sources")
    parser.add_argument("--report-output",
                        type=str,
                        help="Proplaster report archive")
    parser.add_argument(
        "--system-report-config",
        type=str,
        help="Path to the system report yaml config file",
        default=f"{os.path.dirname(system_report_file)}/default_commands.yml")
    parser.add_argument("--sudo", action='store_true', help="Run as sudo")
    parser.add_argument("--server",
                        action='store_true',
                        help="Run in server mode")
    args = parser.parse_args()
    if args.csv_columns and not args.csv and not args.report_output:
        parser.error("--csv-columns requires --csv or --report-output")
    return args


def run_server(args):
    app = Flask(__name__)
    app.config["ARGS"] = args
    app.config["RUN_MANAGER"] = RunManager()
    app.register_blueprint(protoplaster.api.v1.create_routes())
    app.run()


def main():
    args = parse_args()

    if args.sudo:
        os.execv(shutil.which("sudo"),
                 [__file__] + list(filter(lambda a: a != "--sudo", sys.argv)))
    if not os.path.exists(
            f"{args.test_dir}/{args.test_file}") and not args.server:
        print(
            error(
                f"Test file {args.test_dir}/{args.test_file} does not exist or you don't have sufficient permitions"
            ))
        exit(1)
    if args.list_groups:
        list_groups(f"{args.test_dir}/{args.test_file}")
        sys.exit()

    if args.server:
        run_server(args)
    else:
        run_tests(args)


if __name__ == "__main__":
    main()

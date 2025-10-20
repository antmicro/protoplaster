#!/usr/bin/env python3
import argparse
import os
import sys
from colorama import init
from flask import Flask
import shutil

import protoplaster.api.v1
import protoplaster.webui
from protoplaster.conf.consts import CONFIG_DIR, ARTIFACTS_DIR, REPORTS_DIR
from protoplaster.runner.manager import RunManager
from protoplaster.runner.runner import list_tests, list_test_suites, run_tests
from protoplaster.report_generators.system_report.protoplaster_system_report import __file__ as system_report_file
from protoplaster.tools.tools import error


def create_docs_app() -> Flask:
    """Create an app that can be used for building the docs

    This only registers the available API routes, this cannot be used to run
    the server! Used for dynamically building the API reference chapter in
    the documentation.
    """
    app = Flask(__name__)
    app.register_blueprint(protoplaster.api.v1.create_routes())
    return app


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
        "-m",
        "--mkdir",
        action="store_true",
        help="Try to create test/reports/artifacts directories if missing")
    parser.add_argument(
        "-t",
        "--test-file",
        type=str,
        default=f"test.yaml",
        help="Path to the yaml test description in the test directory")
    parser.add_argument("-g",
                        "--group",
                        type=str,
                        help="Group to execute [deprecated]")
    parser.add_argument("-s",
                        "--test-suite",
                        dest="group",
                        metavar="TEST_SUITE",
                        type=str,
                        help="Test suite to execute")
    parser.add_argument("--list-groups",
                        dest="list_test_suites",
                        action="store_true",
                        help="List possible groups to execute [deprecated]")
    parser.add_argument("--list-test-suites",
                        action="store_true",
                        help="List possible test suites to execute")
    parser.add_argument("--list-tests",
                        action="store_true",
                        help="List all defined tests")
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
    parser.add_argument(
        "-l",
        "--log",
        action="store_true",
        help="Append test results to a log file",
    )
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
    parser.add_argument("--port",
                        type=str,
                        default="5000",
                        help="Port to use when running in server mode")
    args = parser.parse_args()
    if args.csv_columns and not args.csv and not args.report_output:
        parser.error("--csv-columns requires --csv or --report-output")
    return args


def run_server(args):
    app = Flask(__name__)
    app.config["ARGS"] = args
    app.config["RUN_MANAGER"] = RunManager()
    app.register_blueprint(protoplaster.api.v1.create_routes())
    app.register_blueprint(protoplaster.webui.webui_blueprint)
    app.run(port=int(args.port))


def main():
    init()
    args = parse_args()

    if args.sudo:
        os.execv(shutil.which("sudo"),
                 [__file__] + list(filter(lambda a: a != "--sudo", sys.argv)))

    if not os.path.exists(args.test_dir):
        if args.mkdir:
            os.makedirs(args.test_dir, exist_ok=True)
        else:
            print(error(f"Tests dir ({args.test_dir}) does not exist!"))
            exit(1)

    if not os.path.exists(args.reports_dir):
        if args.mkdir:
            os.makedirs(args.reports_dir, exist_ok=True)
        else:
            print(error(f"Reports dir ({args.reports_dir}) does not exist!"))
            exit(1)

    if not os.path.exists(args.artifacts_dir):
        if args.mkdir:
            os.makedirs(args.artifacts_dir, exist_ok=True)
        else:
            print(
                error(f"Artifacts dir ({args.artifacts_dir}) does not exist!"))
            exit(1)

    if not os.path.exists(
            f"{args.test_dir}/{args.test_file}") and not args.server:
        print(
            error(
                f"Test file {args.test_dir}/{args.test_file} does not exist or you don't have sufficient permitions"
            ))
        exit(1)
    if args.list_tests:
        list_tests(args)
        sys.exit()
    elif args.list_test_suites:
        list_test_suites(args)
        sys.exit()

    if args.server:
        run_server(args)
    else:
        run_tests(args)


if __name__ == "__main__":
    main()

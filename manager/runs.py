import argparse
import json
import os.path
import requests
from pathlib import Path

StrPath = str | Path


def check_status(response: requests.models.Response):
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.json()['error']}")
        return True
    return False


def test_runs_list(args):
    r = requests.get(f"{args.url}/api/v1/test-runs")
    if check_status(r):
        return
    print("Tests runs on the server:")
    print(json.dumps(r.json(), indent=4))


def test_run_trigger(args):
    params = {
        "config_name": args.test_config,
        "test_suite_name": args.test_suite or ""
    }
    r = requests.post(f"{args.url}/api/v1/test-runs", json=params)
    if check_status(r):
        return
    print("Triggered a test run:")
    print(json.dumps(r.json(), indent=4))


def test_run_info(args):
    r = requests.get(f"{args.url}/api/v1/test-runs/{args.id}")
    if check_status(r):
        return
    print(f"Test info fetched from the server:")
    print(json.dumps(r.json(), indent=4))


def test_run_abort(args):
    r = requests.delete(f"{args.url}/api/v1/test-runs/{args.id}")
    if check_status(r):
        return
    print(f"Test deleted from the server:")
    print(json.dumps(r.json(), indent=4))


def test_run_report(args):
    r = requests.get(f"{args.url}/api/v1/test-runs/{args.id}/report")
    if check_status(r):
        return
    save_path = os.path.join(args.report_dir, f"{args.id}.csv")
    try:
        with open(save_path, "wb") as file:
            file.write(r.content)
        print(f"Report written to {save_path}")
    except Exception as e:
        print(f"Failed to save the report: {str(e)}")


def test_run_artifact(args):
    r = requests.get(
        f"{args.url}/api/v1/test-runs/{args.id}/artifacts/{args.name}")
    if check_status(r):
        return
    save_path = os.path.join(args.artifact_dir, args.name)
    try:
        with open(save_path, "wb") as file:
            file.write(r.content)
        print(f"Artifact written to {save_path}")
    except Exception as e:
        print(f"Failed to save the artifact: {str(e)}")


def add_runs_parser(parser: argparse._SubParsersAction):

    runs = parser.add_parser("runs", help="Test runs management")
    sub = runs.add_subparsers(required=True, title="Test runs commands")

    list = sub.add_parser("list", help="List test runs")
    list.set_defaults(func=test_runs_list)

    run = sub.add_parser("run", help="Trigger a test run")
    run.set_defaults(func=test_run_trigger)
    run.add_argument(
        "--test-config",
        required=True,
        help="Test config name for this test run",
    )
    run.add_argument(
        "--test-suite",
        help="Test suite name for this test run",
    )

    info = sub.add_parser("info", help="Information about a test run")
    info.set_defaults(func=test_run_info)
    info.add_argument("--id", type=str, required=True, help="Test run ID")

    abort = sub.add_parser("abort", help="Abort a pending test run")
    abort.set_defaults(func=test_run_abort)
    abort.add_argument("--id", type=str, required=True, help="Test run ID")

    report = sub.add_parser("report", help="Fetch test run report")
    report.set_defaults(func=test_run_report)
    report.add_argument("--id", type=str, required=True, help="Test run ID")

    artifact = sub.add_parser("artifact", help="Fetch test run artifact")
    artifact.set_defaults(func=test_run_artifact)
    artifact.add_argument("--id", type=str, required=True, help="Test run ID")
    artifact.add_argument("--name",
                          type=str,
                          required=True,
                          help="Artifact name")

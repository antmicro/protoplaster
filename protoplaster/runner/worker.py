from pathlib import Path
from .metadata import RunStatus
from datetime import datetime, timezone
from email.utils import format_datetime
import time
from protoplaster.runner.runner import run_tests
from copy import deepcopy
import os


def load_metadata(artifacts_dir: str, name: str):
    metadata_file = Path(artifacts_dir) / name
    if not metadata_file.exists():
        return None

    with open(metadata_file, "r") as f:
        return f.read().rstrip()


def run_test(run, base_args):
    run["status"] = RunStatus.RUNNING
    run["started_at"] = format_datetime(datetime.now(timezone.utc))

    args = deepcopy(base_args)
    args.test_file = run["config_name"]
    args.group = run["test_suite_name"]
    args.csv = run["id"] + ".csv"
    args.artifacts_dir = os.path.join(args.artifacts_dir, run["id"])

    os.makedirs(args.artifacts_dir, exist_ok=True)

    if not (os.path.exists(args.test_dir) or os.path.exists(args.reports_dir)
            or os.path.exists(args.reports_dir)):
        run["status"] = RunStatus.FAILED
        return

    ret, metadata = run_tests(args)

    run["metadata"] = {
        name: load_metadata(args.artifacts_dir, name)
        for name in metadata
    }

    if ret == 0:
        run["status"] = RunStatus.FINISHED
    else:
        run["status"] = RunStatus.FAILED

    run["finished_at"] = format_datetime(datetime.now(timezone.utc))

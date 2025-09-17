from .metadata import RunStatus
from datetime import datetime, timezone
import time
from protoplaster.runner.runner import run_tests
from copy import deepcopy
import os


def run_test(run, base_args):
    run["status"] = RunStatus.RUNNING
    run["started_at"] = datetime.now(timezone.utc).isoformat()

    args = deepcopy(base_args)
    args.test_file = run["config_name"]
    args.csv = run["id"] + ".csv"
    args.artifacts_dir = os.path.join(args.artifacts_dir, run["id"])

    run_tests(args)

    run["status"] = RunStatus.FINISHED
    run["finished_at"] = datetime.now(timezone.utc).isoformat()

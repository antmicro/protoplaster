from pathlib import Path
from .metadata import RunStatus
from datetime import datetime, timezone
from email.utils import format_datetime
import time
from protoplaster.runner.runner import orchestrate_tests, run_tests, LOCAL_SUCCESS, LOCAL_ERROR
from copy import deepcopy
import os


def load_metadata(artifacts_dir: str, name: str):
    metadata_file = Path(artifacts_dir) / name
    if not metadata_file.exists():
        return None

    with open(metadata_file, "r") as f:
        return f.read().rstrip()


def prepare_args(run_metadata, base_args):
    args = deepcopy(base_args)
    args.test_file = run_metadata["config_name"]
    args.group = run_metadata["test_suite_name"]
    args.csv = run_metadata["id"] + ".csv"
    args.artifacts_dir = os.path.join(args.artifacts_dir, run_metadata["id"])
    args.force_local = run_metadata.get("force_local", False)
    args.overrides = run_metadata["overrides"]

    return args


def run_orchestrator(run_metadata, base_args, orchestrator_data):
    args = prepare_args(run_metadata, base_args)
    orchestrate_tests(args, orchestrator_data)


def run_test(run_metadata, base_args):
    run_metadata["status"] = RunStatus.RUNNING
    run_metadata["started_at"] = format_datetime(datetime.now(timezone.utc))

    args = prepare_args(run_metadata, base_args)
    args.run_obj = run_metadata

    os.makedirs(args.artifacts_dir, exist_ok=True)

    if not (os.path.exists(args.test_dir) or os.path.exists(args.reports_dir)
            or os.path.exists(args.reports_dir)):
        run_metadata["status"] = RunStatus.FAILED
        return

    try:
        ret, metadata = run_tests(args)
    except Exception as e:
        run_metadata["error"] = str(e)
        ret = LOCAL_ERROR
        metadata = []

    run_metadata["metadata"] = {
        name: load_metadata(args.artifacts_dir, name)
        for name in metadata
    }

    if run_metadata.get("abort_requested"):
        run_metadata["status"] = RunStatus.ABORTED
    elif ret == 0:
        run_metadata["status"] = RunStatus.FINISHED
    elif ret == LOCAL_SUCCESS:
        run_metadata["status"] = RunStatus.FINISHED
        run_metadata["hidden"] = True
    else:
        run_metadata["status"] = RunStatus.FAILED

    run_metadata["finished_at"] = format_datetime(datetime.now(timezone.utc))

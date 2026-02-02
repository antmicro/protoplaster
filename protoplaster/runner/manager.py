from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from .metadata import new_run_metadata, RunStatus
from .worker import run_test
from .runner import run_tests, get_target_machines
from datetime import datetime, timezone
from email.utils import format_datetime
from copy import deepcopy


class RunManager:

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.runs = {}
        self.futures = {}
        self.lock = Lock()

    def handle_run_request(self,
                           config_name,
                           test_suite_name,
                           base_args,
                           force_local=False):
        """
        Decides whether to create a tracked local run or bypass it for a remote dispatch.
        """
        # Prepare args for inspection
        check_args = deepcopy(base_args)
        check_args.test_file = config_name
        check_args.group = test_suite_name

        # Check for remote targets
        if not force_local and get_target_machines(check_args):
            return self.run_remote(config_name, test_suite_name, base_args)

        # Otherwise, standard tracked run
        return self.create_run(config_name, test_suite_name, base_args,
                               force_local)

    def create_run(self,
                   config_name: str,
                   test_suite_name: str | None,
                   base_args,
                   force_local=False):

        def on_done(f):
            try:
                f.result()
                print(f"[{run['id']}] completed with status " + run["status"])
            except Exception as e:
                print(f"[{run['id']}] failed: {e}")

        run = new_run_metadata(config_name, test_suite_name)
        run["force_local"] = force_local

        with self.lock:
            self.runs[run["id"]] = run

        future = self.executor.submit(run_test, run, base_args)
        future.add_done_callback(on_done)
        with self.lock:
            self.futures[run["id"]] = future

        return run

    def run_remote(self, config_name, test_suite_name, base_args):
        # Directly submit the runner's entry point to the executor, bypass test creation
        args = deepcopy(base_args)
        args.test_file = config_name
        args.group = test_suite_name

        ret, errors = run_tests(args)
        if ret != 0:
            return {"error": "\n".join(errors)}
        return None

    def get_run(self, run_id: str):
        with self.lock:
            return self.runs.get(run_id)

    def list_runs(self):
        with self.lock:
            return list(self.runs.values())

    def cancel_run(self, run_id: str):
        with self.lock:
            run = self.runs.get(run_id)
            future = self.futures.get(run_id)

        if not run:
            return None

        if run["status"] == RunStatus.PENDING and future:
            future.cancel()
            run["status"] = RunStatus.ABORTED
            run["finished_at"] = format_datetime(datetime.now(timezone.utc))

        return run

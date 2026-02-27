from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from .metadata import new_run_metadata, RunStatus
from .worker import run_test
from .runner import run_tests
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
                           machine_target=None,
                           overrides=[]):
        """
        Decides whether to create a tracked local run or bypass it for a remote dispatch.
        """
        # Prepare args for inspection
        check_args = deepcopy(base_args)
        check_args.test_file = config_name
        check_args.group = test_suite_name
        check_args.overrides = overrides

        # Generate a "tracked" run when it is a result of a remote dispatch.
        if machine_target:
            return self.create_run(config_name, test_suite_name, base_args,
                                   machine_target, overrides)

        # Ochestrator node execution.
        self.executor.submit(run_tests, check_args)
        return None

    def create_run(self,
                   config_name: str,
                   test_suite_name: str | None,
                   base_args,
                   machine_target=None,
                   overrides=[]):

        def on_done(f):
            try:
                f.result()
                print(f"[{run['id']}] completed with status " + run["status"])
            except Exception as e:
                print(f"[{run['id']}] failed: {e}")

        run = new_run_metadata(config_name, test_suite_name, overrides)

        with self.lock:
            self.runs[run["id"]] = run

        # Copy args and inject parameters
        run_args = deepcopy(base_args)
        if machine_target:
            run_args.machine_target = machine_target

        future = self.executor.submit(run_test, run, run_args)
        future.add_done_callback(on_done)
        with self.lock:
            self.futures[run["id"]] = future

        return run

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

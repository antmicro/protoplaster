from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from .metadata import new_run_metadata, RunStatus
from .worker import run_test
from datetime import datetime, timezone


class RunManager:

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.runs = {}
        self.futures = {}
        self.lock = Lock()

    def create_run(self, config_name: str, test_suite_name: str | None,
                   base_args):

        def on_done(f):
            try:
                f.result()
                print(f"[{run['id']}] completed with status " + run["status"])
            except Exception as e:
                print(f"[{run['id']}] failed: {e}")

        run = new_run_metadata(config_name, test_suite_name)
        with self.lock:
            self.runs[run["id"]] = run

        future = self.executor.submit(run_test, run, base_args)
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
            run["finished_at"] = datetime.now(timezone.utc).isoformat()

        return run

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from urllib.parse import urljoin
import uuid
from .metadata import new_run_metadata, RunStatus, new_trigger_metadata
from .worker import run_orchestrator, run_test
from .runner import create_test_file
from datetime import datetime, timezone
from email.utils import format_datetime
from copy import deepcopy
import requests


class OrchestratorData:

    def __init__(self):
        self.trigger_id = str(uuid.uuid4())
        self.triggered_machines = set()


class RunManager:

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.triggers = {}
        self.runs = {}
        self.futures = {}
        self.orchestrators = {}
        self.lock = Lock()

    def handle_run_request(self,
                           config_name,
                           trigger_id,
                           test_suite_name,
                           base_args,
                           machine_target=None,
                           overrides=[],
                           pattern=""):
        # Prepare args for inspection
        check_args = deepcopy(base_args)
        check_args.test_file = config_name
        check_args.group = test_suite_name
        check_args.overrides = overrides

        try:
            create_test_file(check_args)
        except Exception as e:
            return {"error": str(e)}

        run_metadata = new_run_metadata(config_name, trigger_id,
                                        test_suite_name, machine_target,
                                        overrides)

        # if there is no trigger id it means that
        # this is an orchestrator job
        if trigger_id is None:
            orchestrator_data = OrchestratorData()
            self.orchestrators[
                orchestrator_data.trigger_id] = orchestrator_data
            self.create_orchestrator(run_metadata, base_args,
                                     orchestrator_data)
            return None
        else:
            with self.lock:
                trigger = None

                if not trigger_id in self.triggers:
                    trigger = new_trigger_metadata(trigger_id)
                    self.triggers[trigger_id] = trigger
                else:
                    trigger = self.triggers[trigger_id]

                is_aborted = trigger["is_aborted"]

            # Generate a "tracked" run.
            return self.create_run(run_metadata, base_args, is_aborted,
                                   machine_target, pattern)

    def create_orchestrator(self, run_metadata, base_args, orchestrator_data):

        def on_done(f):
            print("Orchestrator finished")

        future = self.executor.submit(run_orchestrator, run_metadata,
                                      base_args, orchestrator_data)
        future.add_done_callback(on_done)

    def create_run(self,
                   run_metadata,
                   base_args,
                   is_aborted,
                   machine_target=None,
                   pattern=""):

        def on_done(f):
            try:
                f.result()
                print(f"[{run_metadata['id']}] completed with status " +
                      run_metadata["status"])
            except Exception as e:
                print(f"[{run_metadata['id']}] failed: {e}")

        with self.lock:
            self.triggers[run_metadata["trigger_id"]]["runs"].append(
                run_metadata)
            self.runs[run_metadata["id"]] = run_metadata

        # Copy args and inject parameters
        run_args = deepcopy(base_args)
        if machine_target:
            run_args.machine_target = machine_target
        if pattern:
            run_args.pattern = pattern

        if not is_aborted:
            future = self.executor.submit(run_test, run_metadata, run_args)
            future.add_done_callback(on_done)
            with self.lock:
                self.futures[run_metadata["id"]] = future
        else:
            run_metadata["status"] = RunStatus.ABORTED

        return run_metadata

    def get_trigger(self, trigger_id: str):
        with self.lock:
            return self.triggers.get(trigger_id)

    def get_run(self, run_id: str):
        with self.lock:
            return self.runs.get(run_id)

    def list_triggers(self):
        with self.lock:
            return list(self.triggers.values())

    def list_runs(self):
        with self.lock:
            return list(self.runs.values())

    def cancel_trigger(self, trigger_id: str):
        with self.lock:
            trigger = self.triggers.get(trigger_id)

            if trigger["is_aborted"]:
                return False

            # set this flag to prevent new tests from running
            trigger["is_aborted"] = True

        canceled_anything = False
        if trigger is not None:
            for run in trigger["runs"]:
                if self.cancel_run(run["id"]):
                    canceled_anything = True

        if not canceled_anything:
            trigger["is_aborted"] = False

        return canceled_anything

    def cancel_run(self, run_id: str):
        with self.lock:
            run = self.runs.get(run_id)
            future = self.futures.get(run_id)

            if not run:
                return False

            if run["status"] == RunStatus.PENDING and future:
                future.cancel()
                run["status"] = RunStatus.ABORTED
                run["finished_at"] = format_datetime(datetime.now(
                    timezone.utc))
                return True
            elif run["status"] == RunStatus.RUNNING:
                run["abort_requested"] = True
                return True

            return False

    def try_cancel_all_running_tests(self, is_server):
        trigger_to_cancel = None

        for run in self.runs.values():
            if run["status"] == RunStatus.RUNNING or run[
                    "status"] == RunStatus.PENDING:
                trigger_to_cancel = run["trigger_id"]
                break

        if not trigger_to_cancel:
            return False

        canceled_anything = self.cancel_trigger(trigger_to_cancel)

        if is_server:
            canceled_anything = False
            orchestrator = self.orchestrators[trigger_to_cancel]
            for mach in orchestrator.triggered_machines:
                try:
                    response = requests.delete(urljoin(
                        mach,
                        f"/api/v1/test-runs/trigger/{trigger_to_cancel}"),
                                               timeout=5)
                    canceled_anything = True
                except Exception:
                    pass

        return canceled_anything

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from urllib.parse import urljoin
import uuid
from .metadata import new_run_metadata, RunStatus, new_trigger_metadata
from protoplaster.conf.consts import LOCAL_DEVICE_HOST
from .worker import run_orchestrator, run_test
from .runner import create_test_file
from datetime import datetime, timezone
from email.utils import format_datetime
from copy import deepcopy
import requests
import shutil
import os


class OrchestratorData:

    def __init__(self,
                 trigger_id=None,
                 run_manager=None,
                 aggregate_results=False,
                 combined_results_dir_prefix=""):
        self.trigger_id = trigger_id
        self.run_manager = run_manager
        self.triggered_machines = {}
        self.aggregate_results = aggregate_results
        self.combined_results_dir_prefix = combined_results_dir_prefix


class RunManager:

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.triggers = {}
        self.runs = {}
        self.futures = {}
        self.orchestrators = {}
        self.orchestrator_futures = {}
        self.lock = Lock()

    def handle_run_request(self,
                           config_name,
                           trigger_id,
                           test_suite_name,
                           base_args,
                           machine_target=None,
                           overrides=[],
                           pattern="",
                           is_orchestrator=False):
        # Prepare args for inspection
        check_args = deepcopy(base_args)
        check_args.test_file = config_name
        check_args.group = test_suite_name
        check_args.overrides = overrides

        try:
            test_file = create_test_file(check_args)
            aggregate_results = test_file.aggregate_results
            combined_results_dir_prefix = test_file.combined_results_dir_prefix
        except Exception as e:
            return {"error": str(e)}

        with self.lock:
            if trigger_id is None:
                trigger_id = str(uuid.uuid4())
                trigger = new_trigger_metadata(trigger_id)
                self.triggers[trigger_id] = trigger
            elif trigger_id not in self.triggers:
                trigger = new_trigger_metadata(trigger_id)
                self.triggers[trigger_id] = trigger
            else:
                trigger = self.triggers[trigger_id]

            is_aborted = trigger["is_aborted"]

        run_metadata = new_run_metadata(config_name, trigger_id,
                                        test_suite_name, machine_target,
                                        overrides)

        if is_orchestrator:
            orchestrator_data = OrchestratorData(
                trigger_id=trigger_id,
                run_manager=self,
                aggregate_results=aggregate_results,
                combined_results_dir_prefix=combined_results_dir_prefix)

            self.orchestrators[trigger_id] = orchestrator_data

            future = self.create_orchestrator(run_metadata, base_args,
                                              orchestrator_data)

            self.orchestrator_futures[trigger_id] = future

        else:
            # Generate a "tracked" run.
            self.create_run(run_metadata, base_args, is_aborted,
                            machine_target, pattern)

        if is_orchestrator:
            return trigger_id

        return run_metadata

    def create_orchestrator(self, run_metadata, base_args, orchestrator_data):

        def on_done(f):
            print(f"Orchestrator {orchestrator_data.trigger_id} finished.")
            if orchestrator_data.aggregate_results:
                print(f"Aggregating results...")
                self.aggregate_results(orchestrator_data.trigger_id, base_args,
                                       orchestrator_data)

        future = self.executor.submit(run_orchestrator, run_metadata,
                                      base_args, orchestrator_data)
        future.add_done_callback(on_done)

        return future

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
            for _, mach_url in orchestrator.triggered_machines:
                try:
                    response = requests.delete(urljoin(
                        mach_url,
                        f"/api/v1/test-runs/trigger/{trigger_to_cancel}"),
                                               timeout=5)
                    canceled_anything = True
                except Exception:
                    pass

        return canceled_anything

    def collect_results(self, trigger_id, base_args, orchestrator_data):
        results = []

        collection_dir = os.path.join(base_args.artifacts_dir,
                                      f"results_{trigger_id}")

        os.makedirs(collection_dir, exist_ok=True)

        local_trigger = self.get_trigger(trigger_id)

        if local_trigger:
            for run in local_trigger["runs"]:
                run_id = run["id"]

                report_path = os.path.join(base_args.reports_dir,
                                           run_id + ".csv")

                artifacts_path = os.path.join(base_args.artifacts_dir, run_id)

                results.append({
                    "machine": LOCAL_DEVICE_HOST,
                    "status": run["status"].value,
                    "report_path": report_path,
                    "artifacts_path": artifacts_path,
                })

        for machine_name, machine_url in (
                orchestrator_data.triggered_machines.items()):

            try:
                resp = requests.get(urljoin(
                    machine_url, f"/api/v1/test-runs/trigger/{trigger_id}"),
                                    timeout=5)

                remote_metadata = resp.json()

                runs = remote_metadata.get("runs", [])

                if not runs:
                    continue

                remote_run = runs[0]
                remote_run_id = remote_run["id"]

                machine_dir = os.path.join(collection_dir, machine_name)

                os.makedirs(machine_dir, exist_ok=True)

                self._download_run_results(machine_name, machine_url,
                                           remote_run_id, machine_dir,
                                           base_args.reports_dir)

                report_path = os.path.join(
                    machine_dir, f"remote_{machine_name}_{remote_run_id}.csv")

                artifacts_path = os.path.join(
                    machine_dir, f"remote_{machine_name}_{remote_run_id}")

                results.append({
                    "machine": machine_name,
                    "status": remote_run["status"],
                    "report_path": report_path,
                    "artifacts_path": artifacts_path,
                })

            except Exception as e:
                print(f"Failed to collect results from {machine_url}: {e}")

        return results

    def aggregate_results(self, trigger_id, base_args, orchestrator_data):
        aggregation_dir = os.path.join(
            base_args.artifacts_dir,
            f"{orchestrator_data.combined_results_dir_prefix}{trigger_id}")
        os.makedirs(aggregation_dir, exist_ok=True)

        local_trigger = self.get_trigger(trigger_id)
        if local_trigger:
            for run in local_trigger["runs"]:
                run_id = run["id"]
                local_artifacts = os.path.join(base_args.artifacts_dir, run_id)
                if os.path.exists(local_artifacts):
                    shutil.copytree(local_artifacts,
                                    os.path.join(aggregation_dir,
                                                 f"local_{run_id}"),
                                    dirs_exist_ok=True)

                local_report = os.path.join(base_args.reports_dir,
                                            run_id + ".csv")
                if os.path.exists(local_report):
                    shutil.copy(
                        local_report,
                        os.path.join(aggregation_dir, f"local_{run_id}.csv"))

        for machine_name, machine_url in orchestrator_data.triggered_machines.items(
        ):
            try:
                resp = requests.get(urljoin(
                    machine_url, f"/api/v1/test-runs/trigger/{trigger_id}"),
                                    timeout=5)

                remote_metadata = resp.json()
                for remote_run in remote_metadata.get("runs", []):
                    remote_run_id = remote_run["id"]
                    self._download_run_results(machine_name, machine_url,
                                               remote_run_id, aggregation_dir,
                                               base_args.reports_dir)
            except Exception as e:
                print(f"Failed to query machine {machine_url}: {e}")

    def _download_run_results(self, machine_name, machine_url, run_id,
                              aggregation_dir, reports_dir):
        run_dest_dir = os.path.join(aggregation_dir,
                                    f"remote_{machine_name}_{run_id}")
        os.makedirs(run_dest_dir, exist_ok=True)

        try:
            report_url = urljoin(machine_url,
                                 f"/api/v1/test-runs/{run_id}/report")
            report_resp = requests.get(report_url, timeout=5)
            if report_resp.status_code == 200:
                with open(
                        os.path.join(aggregation_dir,
                                     f"remote_{machine_name}_{run_id}.csv"),
                        "wb") as f:
                    f.write(report_resp.content)

            artifacts_url = urljoin(machine_url,
                                    f"/api/v1/test-runs/{run_id}/artifacts")
            artifacts_list = requests.get(artifacts_url, timeout=5).json()

            for artifact in artifacts_list:
                artifact_name = artifact["name"]
                file_url = urljoin(
                    machine_url,
                    f"/api/v1/test-runs/{run_id}/artifacts/{artifact_name}")
                file_resp = requests.get(file_url, timeout=5)
                with open(os.path.join(run_dest_dir, artifact_name),
                          "wb") as f:
                    f.write(file_resp.content)
        except Exception as e:
            print(f"Error downloading results for run {run_id}: {e}")

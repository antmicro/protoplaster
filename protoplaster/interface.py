from pathlib import Path
from types import SimpleNamespace
from dataclasses import dataclass
from pathlib import Path

from protoplaster.runner.manager import OrchestratorData, RunManager
from protoplaster.runner.runner import create_test_file, orchestrate_tests
from protoplaster.protoplaster import load_external_devices
from protoplaster.conf.consts import TEST_FILE, CONFIG_DIR, ARTIFACTS_DIR, REPORTS_DIR, LOCAL_DEVICE_NAME, SERVE_IP
from protoplaster.runner.metadata import RunStatus


class Protoplaster:

    def __init__(self,
                 config_dir: str | None = None,
                 reports_dir: str | None = None,
                 artifacts_dir: str | None = None,
                 test_file: str | None = None,
                 external_devices: str | None = None,
                 custom_tests: str | None = None):
        self.config_dir = Path(config_dir) if config_dir else CONFIG_DIR
        self.reports_dir = Path(reports_dir) if reports_dir else REPORTS_DIR
        self.artifacts_dir = Path(
            artifacts_dir) if artifacts_dir else ARTIFACTS_DIR
        self.test_file = test_file if test_file else TEST_FILE
        self.external_devices = external_devices if external_devices else None
        self.custom_tests = custom_tests if custom_tests else None
        self._args = self._build_args()

        self._test_file = create_test_file(self._args)
        self._run_manager = RunManager()
        load_external_devices(self._args)

    def list_tests(self):
        return list(self._test_file.tests.keys())

    def run_tests(self, pattern=None, module_pattern=None):
        """Trigger a test run."""
        self._args.pattern = pattern
        self._args.module_pattern = module_pattern
        trigger_id = self._run_manager.handle_run_request(self.test_file,
                                                          None,
                                                          None,
                                                          self._args,
                                                          is_orchestrator=True)

        return TestRun(self._run_manager, self._args, self.reports_dir,
                       self.artifacts_dir, trigger_id)

    def _build_args(self):
        return SimpleNamespace(
            test_dir=self.config_dir,
            reports_dir=self.reports_dir,
            artifacts_dir=self.artifacts_dir,
            mkdir=True,
            test_file=self.test_file,
            group=None,
            output=None,
            csv=None,
            csv_columns=None,
            generate_docs=False,
            custom_tests=f"{CONFIG_DIR}/tests/*/"
            if self.custom_tests is None else self.custom_tests,
            log=False,
            report_output=None,
            sudo=False,
            server=False,
            dut=False,
            external_devices=self.external_devices,
            overrides=[],
            plugins=None,
            pattern=None,
            module_pattern=None,
            tracked_execution=True)


class TestRun:

    def __init__(self, run_manager, base_args, reports_dir, artifacts_dir,
                 trigger_id):
        self._run_manager = run_manager
        self._reports_dir = reports_dir
        self._artifacts_dir = artifacts_dir
        self.trigger_id = trigger_id
        self._base_args = base_args

    def wait(self, timeout=None):
        orchestrator_future = (
            self._run_manager.orchestrator_futures[self.trigger_id])

        # Wait until orchestration completes
        orchestrator_future.result(timeout=timeout)

        trigger = self._run_manager.triggers[self.trigger_id]

        run_ids = [run["id"] for run in trigger["runs"]]

        futures = [
            self._run_manager.futures[rid] for rid in run_ids
            if rid in self._run_manager.futures
        ]

        # Wait for actual execution
        for future in futures:
            future.result(timeout=timeout)

    def get_id(self):
        trigger = self._run_manager.triggers[self.trigger_id]
        run = trigger["runs"][0]
        return run["id"]

    def results(self):
        orchestrator_data = (self._run_manager.orchestrators[self.trigger_id])

        raw_results = self._run_manager.collect_results(
            self.trigger_id, self._base_args, orchestrator_data)

        results = [
            DeviceResult(
                machine=r["machine"],
                status=r["status"],
                report_path=Path(r["report_path"]),
                artifacts_path=Path(r["artifacts_path"]),
            ) for r in raw_results
        ]

        return TestResults(results=results)


@dataclass
class DeviceResult:
    machine: str
    status: str
    report_path: Path | None
    artifacts_path: Path | None


@dataclass
class TestResults:
    results: list[DeviceResult]

import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from protoplaster.tests.i2c.test import __file__ as i2c_test
from protoplaster.tests.gpio.gpio.test import __file__ as gpio_test
from protoplaster.tests.camera.test import __file__ as camera_test
from protoplaster.tests.fpga.test import __file__ as fpga_test
from protoplaster.tests.network.test import __file__ as network_test
from protoplaster.tests.adc.adc.test import __file__ as adc_test
from protoplaster.tests.adc.LTC2493.test import __file__ as LTC2493_test
from protoplaster.tests.adc.LTC2499.test import __file__ as LTC2499_test
from protoplaster.tests.adc.ADC12DJ3200.test import __file__ as ADC12DJ3200_test
from protoplaster.tests.dac.dac.test import __file__ as dac_test
from protoplaster.tests.dac.ti_dac38j8x_eyescan.test import __file__ as ti_dac38j8x_eyescan_test
from protoplaster.tests.dac.ti_dac38j8x_spi.test import __file__ as ti_dac38j8x_spi_test
from protoplaster.tests.memtester.test import __file__ as mem_test
from protoplaster.tests.dac.LTC2655.test import __file__ as LTC2655_test
from protoplaster.tests.dac.LTC2657.test import __file__ as LTC2657_test
from protoplaster.tests.gpio.PI4IO.test import __file__ as PI4IO_test
from protoplaster.tests.pmic.DA9062.test import __file__ as DA9062_test
from protoplaster.tests.pmic.UCD90320U.test import __file__ as UCD90320U_test
from protoplaster.tests.clock_controller.LMK04828.test import __file__ as LMK04828_test
from protoplaster.tests.thermometer.TMP431.test import __file__ as TMP431_test
from protoplaster.tests.i2c_mux.TCA9548A.test import __file__ as TCA9548A_test
from protoplaster.tests.usb.test import __file__ as usb_test
from protoplaster.tests.simple.test import __file__ as simple_test
from protoplaster.tests.http_echo.test import __file__ as http_echo_test
from protoplaster.tools.tools import pr_err, pr_info, pr_warn

StrPath = str | Path

test_modules_paths = {
    "i2c": i2c_test,
    "gpio": gpio_test,
    "camera": camera_test,
    "fpga": fpga_test,
    "network": network_test,
    "adc": adc_test,
    "LTC2493": LTC2493_test,
    "LTC2499": LTC2499_test,
    "ADC12DJ3200": ADC12DJ3200_test,
    "dac": dac_test,
    "LTC2655": LTC2655_test,
    "LTC2657": LTC2657_test,
    "PI4IO": PI4IO_test,
    "memtester": mem_test,
    "TMP431": TMP431_test,
    "DA9062": DA9062_test,
    "UCD90320U": UCD90320U_test,
    "LMK04828": LMK04828_test,
    "TCA9548A": TCA9548A_test,
    "simple": simple_test,
    "ti_dac38j8x_eyescan": ti_dac38j8x_eyescan_test,
    "ti_dac38j8x_spi": ti_dac38j8x_spi_test,
    "http_echo": http_echo_test,
    "usb": usb_test,
}


def to_path(p: StrPath) -> Path:
    return p if isinstance(p, Path) else Path(p)


def load_yaml(yaml_file: StrPath):
    with open(yaml_file) as file:
        content = yaml.safe_load(file)
    return content


def load_module(module_path: StrPath, module_name: str) -> bool:
    module_path = to_path(module_path) / "test.py"

    if not module_path.is_file():
        pr_warn(f'Additional module "{module_name}" could not be loaded!')
        return False

    file_abs_path = str(module_path.resolve())
    test_modules_paths[module_name] = file_abs_path
    sys.path.append(file_abs_path)

    pr_info(
        f'Additional module loaded "{module_name}" at path {file_abs_path}')

    return True


@dataclass
class ConfigObj:
    name: str
    origin: Path

    def module_path(self) -> str:
        return f"{self.origin.name}::{self.name}"

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, value: object, /) -> bool:
        if not isinstance(value, ConfigObj):
            return NotImplemented
        return self.name == value.name


@dataclass
class TestBody:
    name: str
    module: Path
    params: list[dict[Any]]


@dataclass
class Test(ConfigObj):
    body: list[TestBody]

    def __init__(self, origin: Path, name: str, content: dict[str, Any],
                 test_dir: StrPath, custom_path: StrPath) -> None:
        self.name = name
        self.origin = origin
        self.body = list()

        custom_path = to_path(custom_path)

        is_group = isinstance(content, dict)
        tests = content.get("tests", []) if is_group else content
        group_machines = content.get("machines") if is_group else None

        for entry in tests:
            for module_name, params in entry.items():
                params = (params or {}).copy()

                if group_machines:
                    if "machines" in params:
                        msg = f'{self.origin.name}: "machines" defined in both group "{name}" and test "{module_name}"'
                        pr_err(msg)
                        raise ValueError(msg)
                    params["machines"] = group_machines

                if not ((module_name in test_modules_paths) or (
                    (module_path := to_path(test_dir) / module_name).exists()
                        and load_module(module_path, module_name)) or
                        (custom_path.exists()
                         and load_module(custom_path, module_name))):
                    pr_warn(
                        f'{self.origin.name}: unknown module "{module_name}"')
                    continue

                self.body.append(
                    TestBody(module_name,
                             to_path(test_modules_paths[module_name]), params))


@dataclass
class Metadata(ConfigObj):
    body: dict[str, Any]


@dataclass
class TestSuite(ConfigObj):
    tests: dict[str, Test]
    metadata: dict[str, Metadata]

    def __init__(
        self,
        name: str,
        origin: Path,
        content: dict[str, Any],
        tests: dict[str, Test],
        metadata: dict[str, Metadata],
        test_suites: dict[str, Any],
        *,
        _visited: set | None = None,
        _resolved: dict | None = None,
    ):
        visited = set() if _visited is None else _visited
        resolved = dict() if _resolved is None else _resolved

        self.name = name
        self.origin = origin
        self.tests = dict()
        self.metadata = dict()

        if (local_tests := content.get("tests")) is not None:
            for test in local_tests:
                if test in tests.keys():
                    self.tests[test] = tests[test]
                    continue

                if (test_suite := resolved.get(test)) is not None:
                    self.tests.update(test_suite.tests)
                    continue

                if (test_suites.get(test)) is not None:
                    if test in visited:
                        pr_warn(
                            f'{self.module_path()}: include cycle - "{test}" already included'
                        )
                        continue

                    visited.add(self.name)
                    test_suite = TestSuite(
                        test,
                        origin,
                        content,
                        tests,
                        metadata,
                        test_suites,
                        _visited=visited,
                        _resolved=resolved,
                    )
                    self.tests.update(test_suite.tests)
                    continue

                pr_warn(f'{self.module_path()}: unknown test "{test}"')

        if (local_metadata := content.get("metadata")) is not None:
            for meta in local_metadata:
                if meta in metadata.keys():
                    self.metadata[meta] = metadata[meta]
                    continue

                pr_warn(f'{self.module_path()}: unknown metadata "{meta}"')

        visited.add(self.name)
        resolved[name] = self


@dataclass
class TestFile:
    file: Path

    tests: dict[str, Test]
    metadata: dict[str, Metadata]
    test_suites: dict[str, TestSuite]

    def __init__(
        self,
        test_dir: StrPath,
        yaml_file: StrPath,
        custom_path: StrPath,
        *,
        _visited: set[StrPath] | None = None,
    ) -> None:
        self.file = to_path(test_dir) / yaml_file
        self.tests = dict()
        self.metadata = dict()
        self.test_suites = dict()

        if not self.file.is_file():
            pr_warn(f'{self.file.name}: unknown test file')
            return

        visited = set() if _visited is None else _visited
        visited.add(self.file.name)

        file_content = load_yaml(self.file)

        if (includes := file_content.get("includes")) is not None:
            for include in includes:
                if include in visited:
                    pr_warn(
                        f'{self.file.name}: include cycle - file "{include}" already included'
                    )
                    continue

                include_file = TestFile(test_dir,
                                        include,
                                        custom_path,
                                        _visited=visited)
                self.tests.update(include_file.tests)
                self.metadata.update(include_file.metadata)
                self.test_suites.update(include_file.test_suites)

        if (tests := file_content.get("tests")) is not None:
            for name, content in tests.items():
                test = Test(self.file, name, content, test_dir, custom_path)

                if name in self.tests.keys():
                    pr_warn(
                        f'{test.module_path()}: test redefined (previous definition in {self.tests[name].module_path()})'
                    )

                self.tests[name] = Test(self.file, name, content, test_dir,
                                        custom_path)

        if (metadata := file_content.get("metadata")) is not None:
            for name, content in metadata.items():
                metadata = Metadata(name, self.file, content)

                if name in self.metadata.keys():
                    pr_warn(
                        f'{metadata.module_path()}: metadata redefined (previous definition in {self.metadata[name].module_path()})'
                    )

                self.metadata[name] = metadata

        if (test_suites := file_content.get("test-suites")) is not None:
            for name, content in test_suites.items():
                if name in self.tests.keys():
                    pr_err(
                        f'{self.file.name}::{name}: test-suite conflicts with test {self.tests[name].module_path()}'
                    )
                    continue

                if name in self.test_suites.keys():
                    pr_warn(
                        f'{self.file.name}::{name}: test-suite redefined (previous definition in {self.test_suites[name].module_path()})'
                    )

                self.test_suites[name] = TestSuite(
                    name,
                    self.file,
                    content,
                    self.tests,
                    self.metadata,
                    test_suites,
                    _resolved=self.test_suites,
                )

    def filter_suite(self, suite: str):
        if suite not in self.test_suites.keys():
            pr_err(f'Unknown test suite "{suite}"')
            return

        target_suite = self.test_suites[suite]
        self.tests = target_suite.tests
        self.metadata = target_suite.metadata
        self.test_suites = {suite: target_suite}

    def filter_runnable_tests(self, target: str | None):
        """
        Keeps tests with NO 'machines' defined if the `target` is None, otherwise keep tests where 'machines' includes the target
        """
        for name, test in list(self.tests.items()):
            test.body = [b for b in test.body if self._should_run(b, target)]
            if not test.body:
                del self.tests[name]

    def _should_run(self, body: TestBody, target: str | None) -> bool:
        machines = body.params.get("machines")
        if not machines:
            return target is None

        if isinstance(machines, str):
            machines = [machines]

        return target in machines if target else False

    def get_all_machines(self) -> set[str]:
        machines = set()
        for test in self.tests.values():
            for body in test.body:
                ms = body.params.get("machines")
                if ms:
                    machines.update([ms] if isinstance(ms, str) else ms)
        return machines

    def list_test_modules(self) -> list[str]:
        modules = []

        for test in self.tests.values():
            modules += [str(body.module.resolve()) for body in test.body]

        return modules

    def list_metadata_commands(self) -> dict[str, Any]:
        return {value.name: value.body for value in self.metadata.values()}

    def merged_test_file(self) -> tempfile._TemporaryFileWrapper:
        test_runner_fmt = dict()

        for test in self.tests.values():
            test_runner_fmt[test.name] = [{
                value.name: value.params
            } for value in test.body]

        test_file = tempfile.NamedTemporaryFile("w",
                                                suffix=".yml",
                                                prefix="protoplaster-")
        yaml.safe_dump(test_runner_fmt, test_file)

        return test_file

import ast
import os
import sys
import time
import uuid
import zipfile
import requests
import copy
import importlib
import inspect
from urllib.parse import urljoin
from pathlib import Path
from typing import Set, get_type_hints

import pytest
from jinja2 import Environment, DictLoader, select_autoescape

from protoplaster.docs.docs import Hint, TestDocs
from protoplaster.docs import __file__ as docs_path

from protoplaster.conf.csv_generator import CsvReportGenerator
from protoplaster.conf.log_generator import LogGenerator
from protoplaster.conf.parser import TestFile, load_yaml, CustomizedLoader, test_modules_paths
from protoplaster.report_generators.test_report.protoplaster_test_report import generate_test_report
from protoplaster.report_generators.system_report.protoplaster_system_report import generate_system_report, CommandConfig, run_command
from protoplaster.tools.log import error, pr_warn, pr_err, warning
from protoplaster.webui.devices import get_all_devices
from protoplaster.conf.consts import REMOTE_RUN_TRIGGER_TIMEOUT, SERVE_IP, WEBUI_POLLING_INTERVAL, LOCAL_DEVICE_HOST
from protoplaster import __file__ as protoplaster_root


class PytestAbortPlugin:
    """Plugin to gracefully abort pytest execution between tests if requested."""

    def __init__(self, run_obj):
        self.run_obj = run_obj

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(self, item):
        if self.run_obj and self.run_obj.get("abort_requested"):
            pytest.exit("Aborted by user")


TOP_LEVEL_TEMPLATE_PATH = "template.md"
REMOTE_TEST_POLL_INTERVAL = 1
"""
Test runs triggered from the web UI are special: they
split config files into test suites and trigger secondary runs.
For the ability to report errors, they are tracked normally
and only shown to the user if they exit with an error.
We introduce two custom exit codes to implement this behavior.
"""
LAST_PYTEST_EXIT_CODE = list(pytest.ExitCode)[-1]._value_
LOCAL_SUCCESS = LAST_PYTEST_EXIT_CODE + 1
LOCAL_ERROR = LAST_PYTEST_EXIT_CODE + 2


def create_test_file(args) -> TestFile:
    overrides = copy.copy(args.overrides)
    # CustomizedLoader is a modified YAML loader class that remembers anchors
    # between parsed files. Calls to _reset_custom() are necessary to reset
    # the internal structures between parsing files that are actually
    # semantically separate.
    with CustomizedLoader._reset_custom():
        test_file = TestFile(args.test_dir, args.test_file, args.custom_tests,
                             overrides)
    if len(overrides) > 0:
        pr_err(f"These overrides could not be applied: {overrides}")
    if (group := args.group) not in (None, ""):
        test_file.filter_suite(group)
    if (pattern := args.module_pattern) not in (None, ""):
        test_file.filter_pattern(pattern)

    return test_file


def list_tests(args):
    test_file = create_test_file(args)
    for test in test_file.tests.keys():
        print(test)


def list_test_suites(args):
    test_file = create_test_file(args)

    for name, suite in test_file.test_suites.items():
        print(f"{name}:")
        for test in suite.tests.keys():
            print(f"- {test}")


def label(label: str, value=None) -> str:
    # function for use in Jinja templates
    if value:
        return f"`{label}`: *{value}*"
    return f"`{label}`"


def generate_rst_doc(tests_doc_list, docs_dict, output_file):

    jinja2_env = Environment(
        loader=DictLoader(docs_dict),
        autoescape=select_autoescape(),
        extensions=[
            "jinja2.ext.do",
        ],
        lstrip_blocks=True,
    )
    jinja2_env.globals["label"] = label

    template = jinja2_env.get_template(TOP_LEVEL_TEMPLATE_PATH)
    output = template.render(tests_doc_list=tests_doc_list)
    with open(output_file, "w") as doc:
        doc.write(output)


def typename(t) -> str:
    # print name of type
    if isinstance(t, type):
        return t.__name__
    else:
        return str(t)


def traverse_annotations(nodes: dict) -> list[Hint]:
    """
    Recursively collect Hint objects from type annotations and fill empty attributes

    `nodes` is dictionary returned by get_type_hints(class, include_extras=True)
    or dictionary of classes mapped to ignored placeholder values

    Example of final effect:
    devices: list[Device], required
      List of devices to test
      Device
        (type with attributes defined below)
        path: str
          Path to device
    """
    if not nodes:
        return []
    children = []
    for node_name in nodes:
        name = node_name if isinstance(node_name, str) else ""
        if hasattr(nodes[node_name], "__args__"):
            # if node is an Annotated[] or a subscripted type
            datatype = nodes[node_name].__args__
            # recurse into the node's datatype (this is how the "Device"
            # class was annotated in the example above)
            children_next = traverse_annotations(dict(enumerate(datatype)))
            datatype = ", ".join(typename(t) for t in datatype)
            hint = getattr(nodes[node_name], "__metadata__", (None, ))[0]
            if hint and not isinstance(hint, Hint):
                # node is an Annotated[] and its 2nd argument is not a Hint object
                raise ValueError(name)
            if hint is None:
                # node is a subscripted type (for example list[Device]);
                # create a Hint object for a class with further attributes
                hint = Hint("")
            hint.name, hint.datatype = name, datatype
            for c in children_next:
                # ignore nodes with no content; otherwise, for example,
                # list[str] would cause "str" to needlessly appear in docs
                # with no description and no children
                if c.description or c.children:
                    hint.children = (getattr(hint, "children") or []) + [c]
            children.append(hint)
        else:
            # if node is a class (like Device in example above)
            hints = get_type_hints(nodes[node_name], include_extras=True)
            children_next = traverse_annotations(hints)
            children += children_next
    return children


def generate_docs(yaml_content=None) -> None:
    tests_doc_list = []
    templates = {}
    mod_testcls = {}
    method_macros: dict[str, list[str]] = {}
    parameters = {}

    with open(f"{os.path.dirname(docs_path)}/{TOP_LEVEL_TEMPLATE_PATH}",
              "r") as jinja2_doc:
        templates[TOP_LEVEL_TEMPLATE_PATH] = jinja2_doc.read()

    def is_test_function(f):
        return inspect.isfunction(f) and f.__name__.startswith("test")

    for test_path in test_modules_paths.values():
        module_name = Path(test_path).parent.stem
        spec = importlib.util.spec_from_file_location(module_name, test_path)
        if spec is None or spec.loader is None:
            sys.exit(error(f'Could not import {test_path} - Exiting!'))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def is_test_class(cls):
            return inspect.isclass(cls) and getattr(
                cls, "module_name", lambda: None)() == module_name

        for cls_name, cls in inspect.getmembers(module, is_test_class):
            class_doc = inspect.getdoc(cls)
            if not class_doc:
                sys.exit(
                    error(f'Docstring for the "{cls_name}" class ' +
                          'is not defined - Exiting!'))
            elif cls_name not in class_doc:
                sys.exit(
                    error(f'Macro in the docstring for the "{cls_name}" ' +
                          'class should have the same name ' + '- Exiting!'))
            templates[cls_name] = class_doc

            annotations = get_type_hints(cls, include_extras=True)
            try:
                parameters[cls_name] = traverse_annotations(annotations)
            except ValueError as e:
                sys.exit(
                    error(
                        f'Incorrect type annotation in class "{cls_name}": {e} - Exiting!'
                    ))

            for func_name, func in inspect.getmembers(cls, is_test_function):
                function_doc = inspect.getdoc(func) or ""
                if not function_doc:
                    sys.exit(
                        error(
                            f'Docstring for the "{func.__name__}" function ' +
                            f'in class {cls_name} is not defined - Exiting!'))
                elif func.__name__ not in function_doc:
                    sys.exit(
                        error(
                            f'Macro in the docstring for the "{func.__name__}" '
                            + f'function in class "{cls_name}" should ' +
                            'have the same name as function - Exiting!'))
                templates[cls_name] += function_doc
                method_macros.setdefault(cls_name, []).append(func.__name__)
            # map module names to test class names
            mod_testcls[test_path.split("/")[-2]] = cls_name

    if yaml_content is not None:
        # collect data from yaml file
        for test_group in yaml_content:
            for test_module in yaml_content[test_group]:
                mod_name, mod_conf = next(iter(test_module.items()))
                cls_name = mod_testcls[mod_name]
                test_doc = TestDocs(
                    cls_name, sorted(parameters[cls_name],
                                     key=lambda x: x.name), mod_conf,
                    method_macros[cls_name])
                tests_doc_list.append(test_doc)
        output_file = "tests_description.md"
    else:
        # generate docs for all tests
        for cls_name in mod_testcls.values():
            mod_conf = {}
            for p in parameters[cls_name]:
                # avoid errors when using dictionaries in docstrings
                if p.datatype.startswith("dict") or (p.children and all(
                        d.name for d in p.children)):
                    mod_conf[p.name] = {}
            test_doc = TestDocs(
                cls_name, sorted(parameters[cls_name], key=lambda x: x.name),
                mod_conf, method_macros[cls_name])
            tests_doc_list.append(test_doc)
        output_file = "tests_reference.md"
    generate_rst_doc(tests_doc_list, templates, output_file)


def extract_class_names(path):
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and getattr(
                        decorator.func, 'id', '') == 'ModuleName':
                    classes.append(node.name)
                    break

    return classes


def prepare_pytest_args(test_paths, args, test_file_path):
    pytest_args = f" --keep-duplicates -s -p no:cacheprovider -p protoplaster.conf.params_conf --yaml_file={test_file_path} --instafail "
    if args.output:
        pytest_args += f"--junitxml={args.output} "
    if args.artifacts_dir:
        pytest_args += f"--artifacts-dir={args.artifacts_dir} "

    if getattr(args, 'machine_target', None):
        pytest_args += f"--machine-target={args.machine_target} "

    unique_tests = set()
    test_to_run = ""

    for test_path in test_paths:
        classes = extract_class_names(test_path)
        if len(classes) == 0:
            pr_warn(f"'{test_path}' has no class with @ModuleName to test")
            continue
        test_class = classes[0]
        if len(classes) > 1:
            pr_warn(
                f"'{test_path}' has more than one class to test. Choosing first one: '{test_class}'"
            )

        # Deduplicate based on the specific class in the file
        key = f"{test_path}::{test_class}"
        if key not in unique_tests:
            unique_tests.add(key)
            test_to_run += f" {key}"

    pytest_args = test_to_run + pytest_args
    pytest_args = pytest_args.strip().split(" ")
    # Processing pattern separately as it might contain whitespaces
    if hasattr(args, "pattern") and args.pattern is not None and len(
            args.pattern):
        pytest_args.append(f'-k={args.pattern}')
    return pytest_args


def generate_metadata(args, metadata_cmds):

    cmd_results = []
    for cmd in metadata_cmds.items():
        cmd[1]["output"] = cmd[0]
        command_config = CommandConfig(cmd)
        result = run_command(command_config)
        cmd_results.append(result)
        with open(os.path.join(args.artifacts_dir, result.output_file),
                  "w") as f:
            f.write(result.raw_output)

    return cmd_results


def _trigger_remote_run(machine, base_url, args, group):
    print(f"Triggering run on {machine} ({base_url})")

    config_name = os.path.basename(args.test_file)
    payload = {
        "config_name": config_name,
        "trigger_id": args.trigger_id,
        "test_suite_name": group,
        "machine_target": machine
    }

    overrides = getattr(args, "overrides", [])
    if overrides:
        payload["overrides"] = "\n".join(overrides)

    try:
        response = requests.post(urljoin(base_url, "/api/v1/test-runs"),
                                 json=payload,
                                 timeout=REMOTE_RUN_TRIGGER_TIMEOUT)
        response.raise_for_status()
        run_data = response.json()
        run_id = run_data.get('id')
        print(f"[{machine}] Remote run triggered successfully. ID: {run_id}")
        return run_id
    except Exception as e:
        err_msg = f"[{machine}] Failed to trigger run: {e}"
        print(error(err_msg))
        return None


def wait_for_remote_runs(remote_runs):
    if not remote_runs:
        return

    print("Waiting for remote tests to finish...")
    completed_runs = set()

    while len(completed_runs) < len(remote_runs):
        for run_info in remote_runs:
            machine = run_info["machine"]

            if machine in completed_runs:
                continue

            # Local tracked execution
            future = run_info.get("future")
            if future is not None:
                if future.done():
                    try:
                        future.result()
                        print(f"[{machine}] Local run finished successfully")

                    except Exception as e:
                        print(error(f"[{machine}] Local run failed: {e}"))

                    completed_runs.add(machine)

                continue

            # Remote HTTP execution
            run_id = run_info["run_id"]
            base_url = run_info["base_url"]

            try:
                response = requests.get(urljoin(base_url,
                                                f"/api/v1/test-runs/{run_id}"),
                                        timeout=5)
                response.raise_for_status()
                status = response.json().get("status")

                if status in ["finished", "failed", "aborted"]:
                    print(
                        f"[{machine}] Remote run {run_id} finished with status: {status}"
                    )
                    completed_runs.add(machine)
            except Exception as e:
                print(error(f"[{machine}] Failed to get run status: {e}"))
                completed_runs.add(machine)

        if len(completed_runs) < len(remote_runs):
            time.sleep(REMOTE_TEST_POLL_INTERVAL)


def get_target_machines(args) -> Set:
    test_file = create_test_file(args)
    return test_file.get_all_machines()


def has_local_tests(args) -> bool:
    test_file = create_test_file(args)
    test_file.filter_runnable_tests(None)
    return len(test_file.tests) > 0


def orchestrate_tests(args, orchestrator_data):
    devices = {d['name']: d['url'] for d in get_all_devices()}
    test_file = create_test_file(args)

    args.trigger_id = orchestrator_data.trigger_id
    for test_name, test_obj in test_file.tests.items():
        print(f"Executing test group: {test_name}")
        args.group = test_name

        machines = set()
        has_local = False
        for body in test_obj.body:
            ms = body.params.get("machines")
            if ms:
                machines.update([ms] if isinstance(ms, str) else ms)
            else:
                has_local = True

        remote_runs = []
        for machine in machines:
            if machine in devices:
                mach_url = devices[machine]
                orchestrator_data.triggered_machines[machine] = mach_url

                run_id = _trigger_remote_run(machine, mach_url, args,
                                             test_name)
                if run_id:
                    remote_runs.append({
                        "machine": machine,
                        "base_url": devices[machine],
                        "run_id": run_id
                    })
            else:
                print(
                    error(f"Machine '{machine}' not defined in devices list"))

        if has_local:
            if getattr(args, "server", False):
                # Web server mode: Dispatch to the local Flask server
                local_url = f"http://{SERVE_IP}:{args.port}"
                run_id = _trigger_remote_run(LOCAL_DEVICE_HOST, local_url,
                                             args, test_name)
                if run_id:
                    remote_runs.append({
                        "machine": LOCAL_DEVICE_HOST,
                        "base_url": local_url,
                        "run_id": run_id
                    })
            elif getattr(args, "tracked_execution", False):
                run_metadata = orchestrator_data.run_manager.handle_run_request(
                    config_name=args.test_file,
                    trigger_id=args.trigger_id,
                    test_suite_name=test_name,
                    base_args=args,
                    machine_target=LOCAL_DEVICE_HOST,
                    is_orchestrator=False,
                )
                remote_runs.append({
                    "machine":
                    LOCAL_DEVICE_HOST,
                    "future":
                    orchestrator_data.run_manager.futures[run_metadata["id"]]
                })
            else:
                # CLI mode: Execute local tests directly
                print("Executing local tests directly (CLI mode)")

                csv = getattr(args, "csv", None)
                if csv:
                    csv_name, csv_ext = os.path.splitext(csv)
                    modified_csv = f"{csv_name}_{test_name}{csv_ext}"
                    csv = modified_csv
                    print(
                        warning(
                            f"Multiple test runs detected in CLI mode. Report for group '{test_name}' will be saved to: {modified_csv}"
                        ))

                run_tests(args, LOCAL_DEVICE_HOST, csv)

        wait_for_remote_runs(remote_runs)


def run_tests(args, machine_target, csv):
    if args.generate_docs:
        test_file = create_test_file(args)
        paths_to_tests = test_file.list_paths_to_tests()
        with test_file.merged_test_file() as tf:
            generate_docs(load_yaml(tf.name))
            sys.exit()

    if machine_target == LOCAL_DEVICE_HOST:
        machine_target = None
        args.machine_target = None

    # Filter tests for execution on "local" node
    test_file = create_test_file(args)
    test_file.filter_runnable_tests(machine_target)

    paths_to_tests = test_file.list_paths_to_tests()
    metadata_cmds = test_file.list_metadata_commands()

    if metadata_cmds:
        metadata = [
            result.output_file
            for result in generate_metadata(args, metadata_cmds)
        ]
    else:
        metadata = []

    if not paths_to_tests:
        return 0, metadata

    with test_file.merged_test_file() as tf:
        plugins = []
        csv_report_gen = CsvReportGenerator(args.csv_columns, metadata)
        plugins.append(csv_report_gen)

        if args.log:
            log_report_gen = LogGenerator(
                f"{args.artifacts_dir}/protoplaster.log")
            plugins.append(log_report_gen)

        # Inject a plugin that runs before every test in a test module to check
        # if the `abort_requested` field is set.
        if getattr(args, "run_obj", None):
            plugins.append(PytestAbortPlugin(args.run_obj))

        ret = pytest.main(prepare_pytest_args(paths_to_tests, args, tf.name),
                          plugins=plugins)
    if csv:
        with open(f"{args.reports_dir}/{csv}", "w") as csv_file:
            csv_file.write(csv_report_gen.report)
    if args.report_output:
        with open(args.report_output, "wb") as archive_file:
            with zipfile.ZipFile(archive_file, 'w',
                                 zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("test_report.csv", csv_report_gen.report)
                archive.writestr(
                    "test_report.html",
                    generate_test_report(csv_report_gen.report, "html"))

                for filename, content in generate_system_report(
                        args.system_report_config):
                    archive.writestr(filename, content)
    return ret, metadata

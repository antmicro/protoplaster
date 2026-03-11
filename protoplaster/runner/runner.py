import ast
import os
import sys
import time
import zipfile
import requests
import copy
from urllib.parse import urljoin
from collections import OrderedDict
from pathlib import Path
from typing import Optional, Set

import pytest
from jinja2 import Environment, DictLoader, select_autoescape

from protoplaster.docs.docs import TestDocs
from protoplaster.docs import __file__ as docs_path

from protoplaster.conf.csv_generator import CsvReportGenerator
from protoplaster.conf.log_generator import LogGenerator
from protoplaster.conf.parser import TestFile, load_yaml
from protoplaster.report_generators.test_report.protoplaster_test_report import generate_test_report
from protoplaster.report_generators.system_report.protoplaster_system_report import generate_system_report, CommandConfig, run_command
from protoplaster.tools.log import error, pr_warn, pr_err, warning
from protoplaster.webui.devices import get_all_devices
from protoplaster.conf.consts import REMOTE_RUN_TRIGGER_TIMEOUT, SERVE_IP, WEBUI_POLLING_INTERVAL, LOCAL_DEVICE_HOST
from protoplaster import __file__ as protoplaster_root

TOP_LEVEL_TEMPLATE_PATH = "template.md"
REMOTE_TEST_POLL_INTERVAL = 1


def create_test_file(args) -> TestFile:
    overrides = copy.copy(args.overrides)
    test_file = TestFile(args.test_dir, args.test_file, args.custom_tests,
                         overrides)
    if len(overrides) > 0:
        pr_err(f"These overrides could not be applied: {overrides}")
    if (group := args.group) not in (None, ""):
        test_file.filter_suite(group)

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


def generate_rst_doc(tests_doc_list, docs_dict):

    jinja2_env = Environment(
        loader=DictLoader(docs_dict),
        autoescape=select_autoescape(),
        extensions=[
            "jinja2.ext.do",
        ],
        lstrip_blocks=True,
    )

    template = jinja2_env.get_template(TOP_LEVEL_TEMPLATE_PATH)
    output = template.render(tests_doc_list=tests_doc_list)
    with open("protoplaster.md", "w") as doc:
        doc.write(output)


def generate_docs(tests_full_path, yaml_content):
    tests_doc_list = []
    templates = {}
    mod_testcls = {}
    method_macros = {}

    with open(f"{os.path.dirname(docs_path)}/{TOP_LEVEL_TEMPLATE_PATH}",
              "r") as jinja2_doc:
        templates[TOP_LEVEL_TEMPLATE_PATH] = jinja2_doc.read()

    for test_path in tests_full_path:
        # collect docstrings from tests
        py_file = Path(test_path)
        raw_tree = py_file.read_text()
        tree = ast.parse(raw_tree)
        classes = [c for c in ast.walk(tree) if isinstance(c, ast.ClassDef)]
        for tests_class in classes:
            class_doc = ast.get_docstring(tests_class)
            if class_doc is None:
                print(
                    error(f'Docstring for the "{tests_class.name}" class ' +
                          'is not defined - Exiting!'))
                sys.exit(2)
            elif tests_class.name not in class_doc:
                print(
                    error(
                        f'Macro in the docstring for the "{tests_class.name}" '
                        + 'function should have the same name as class ' +
                        '- Exiting!'))
                sys.exit(3)
            templates[tests_class.name] = class_doc

            functions = [
                f for f in ast.walk(tests_class)
                if isinstance(f, ast.FunctionDef) and f.name.startswith("test")
            ]
            for func in functions:
                function_doc = ast.get_docstring(func)
                if function_doc is None:
                    print(
                        error(
                            f'Docstring for the "{func.name}" function ' +
                            f'in class {tests_class.name} is not defined - Exiting!'
                        ))
                    sys.exit(4)
                elif func.name not in function_doc:
                    print(
                        error(
                            f'Macro in the docstring for the "{func.name}" ' +
                            f'function in class "{tests_class.name}" should ' +
                            'have the same name as function - Exiting!'))
                    sys.exit(5)
                templates[tests_class.name] += function_doc
                method_macros.setdefault(tests_class.name,
                                         []).append(func.name)
            # map module names to test class names
            mod_testcls[test_path.split("/")[-2]] = tests_class.name
    # collect data from yaml file
    for test_group in yaml_content:
        for test_module in yaml_content[test_group]:
            mod_name, mod_conf = next(iter(test_module.items()))
            cls_name = mod_testcls[mod_name]
            test_doc = TestDocs(cls_name, mod_conf, method_macros[cls_name])
            tests_doc_list.append(test_doc)
    generate_rst_doc(tests_doc_list, templates)


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


def prepare_pytest_args(test_paths, args):
    pytest_args = f" --keep-duplicates -s -p no:cacheprovider -p protoplaster.conf.params_conf --yaml_file={args.test_file} "
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
    return pytest_args.strip().split(" ")


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


def _trigger_remote_run(machine, base_url, args):
    print(f"Triggering run on {machine} ({base_url})")

    config_name = os.path.basename(args.test_file)
    payload = {
        "config_name": config_name,
        "test_suite_name": args.group,
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
            run_id = run_info["run_id"]
            if run_id in completed_runs:
                continue

            machine = run_info["machine"]
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
                    completed_runs.add(run_id)
            except Exception as e:
                print(error(f"[{machine}] Failed to get run status: {e}"))
                completed_runs.add(run_id)

        if len(completed_runs) < len(remote_runs):
            time.sleep(REMOTE_TEST_POLL_INTERVAL)


def get_target_machines(args) -> Set:
    test_file = create_test_file(args)
    return test_file.get_all_machines()


def has_local_tests(args) -> bool:
    test_file = create_test_file(args)
    test_file.filter_runnable_tests(None)
    return len(test_file.tests) > 0


def run_tests(args):
    # Check execution context:
    # - <string>: Triggered by a `_trigger_remote_run` call from the orchestrator.
    #             Act as a DUT node, running ONLY the tests assigned to this specific node.
    # - None:     Act as the orchestrator, dispatching remote tests and running local ones.
    machine_target = getattr(args, "machine_target", None)

    if args.generate_docs:
        test_file = create_test_file(args)
        paths_to_tests = test_file.list_paths_to_tests()
        with test_file.merged_test_file() as tf:
            generate_docs(
                OrderedDict.fromkeys(paths_to_tests).keys(),
                load_yaml(tf.name))
            sys.exit()

    if not machine_target:
        devices = {d['name']: d['url'] for d in get_all_devices()}
        test_file = create_test_file(args)

        for test_name, test_obj in test_file.tests.items():
            print(f"Executing test group: {test_name}")
            chunk_args = copy.copy(args)
            chunk_args.group = test_name

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
                    run_id = _trigger_remote_run(machine, devices[machine],
                                                 chunk_args)
                    if run_id:
                        remote_runs.append({
                            "machine": machine,
                            "base_url": devices[machine],
                            "run_id": run_id
                        })
                else:
                    print(
                        error(
                            f"Machine '{machine}' not defined in devices list")
                    )

            if has_local:
                if getattr(args, "server", False):
                    # Web server mode: Dispatch to the local Flask server
                    local_url = f"http://{SERVE_IP}:{args.port}"
                    run_id = _trigger_remote_run(LOCAL_DEVICE_HOST, local_url,
                                                 chunk_args)
                    if run_id:
                        remote_runs.append({
                            "machine": LOCAL_DEVICE_HOST,
                            "base_url": local_url,
                            "run_id": run_id
                        })
                else:
                    # CLI mode: Execute local tests directly
                    print("Executing local tests directly (CLI mode)")
                    local_chunk_args = copy.copy(chunk_args)
                    local_chunk_args.machine_target = LOCAL_DEVICE_HOST

                    if getattr(local_chunk_args, "csv", None):
                        csv_name, csv_ext = os.path.splitext(
                            local_chunk_args.csv)
                        modified_csv = f"{csv_name}_{test_name}{csv_ext}"
                        local_chunk_args.csv = modified_csv
                        print(
                            warning(
                                f"Multiple test runs detected in CLI mode. Report for group '{test_name}' will be saved to: {modified_csv}"
                            ))

                    run_tests(local_chunk_args)

            wait_for_remote_runs(remote_runs)

        return 0, []

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
        args.test_file = tf.name

        plugins = []
        csv_report_gen = CsvReportGenerator(args.csv_columns, metadata)
        plugins.append(csv_report_gen)

        if args.log:
            log_report_gen = LogGenerator(
                f"{args.artifacts_dir}/protoplaster.log")
            plugins.append(log_report_gen)
        ret = pytest.main(prepare_pytest_args(paths_to_tests, args),
                          plugins=plugins)
    if args.csv:
        with open(f"{args.reports_dir}/{args.csv}", "w") as csv_file:
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

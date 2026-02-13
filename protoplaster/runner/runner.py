import ast
import os
import sys
import zipfile
import requests
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
from protoplaster.tools.tools import error, pr_warn, warning
from protoplaster.webui.devices import get_all_devices
from protoplaster.conf.consts import REMOTE_RUN_TRIGGER_TIMEOUT
from protoplaster import __file__ as protoplaster_root

TOP_LEVEL_TEMPLATE_PATH = "template.md"


def create_test_file(args) -> TestFile:
    test_file = TestFile(args.test_dir, args.test_file, args.custom_tests)
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

    with open(f"{os.path.dirname(docs_path)}/{TOP_LEVEL_TEMPLATE_PATH}",
              "r") as jinja2_doc:
        templates[TOP_LEVEL_TEMPLATE_PATH] = jinja2_doc.read()

    for test_path in tests_full_path:
        module_details = []
        method_macros = []

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
                        error(f'Docstring for the "{func.name}" function ' +
                              'is not defined - Exiting!'))
                    sys.exit(4)
                elif func.name not in function_doc:
                    print(
                        error(
                            f'Macro in the docstring for the "{func.name}" ' +
                            'function should have the same name as function ' +
                            '- Exiting!'))
                    sys.exit(5)
                templates[tests_class.name] += function_doc
                method_macros.append(func.name)
            # collect data from yaml file
            for test_group in yaml_content:
                for test_module in yaml_content[test_group]:
                    module = test_path.split("/")
                    if module[-2] == test_module:
                        module_details.append(
                            yaml_content[test_group][test_module])

            test_doc = TestDocs(tests_class.name, module_details,
                                method_macros)
            tests_doc_list.append(test_doc)
    generate_rst_doc(tests_doc_list, templates)


def create_links_to_tests(paths_to_tests):
    """
    Creates symlinks for the given test files under 'symlinks/{test_index}'.

    This is a workaround to force pytest to collect the same test class
    multiple times. Pytest normally executes `setup_class` only once when
    the same class is selected multiple times using identical node IDs,
    for example:

        pytest protoplaster/test.py::TestClassA \
               protoplaster/test.py::TestClassA

    By creating symlinks, each test file gets a different path, which
    results in different node IDs, for example:

        pytest protoplaster/symlinks/1/test.py::TestClassA \
               protoplaster/symlinks/2/test.py::TestClassA

    This forces pytest to treat them as separate test classes and execute
    `setup_class` for each instance.

    The directory structure relative to the project root is preserved.
    """
    protoplaster_dir = Path(protoplaster_root).parent
    symlinks_dir = protoplaster_dir / "symlinks"
    symlinks_dir.mkdir(exist_ok=True)

    links_to_test = []
    for i, path_to_test in enumerate(paths_to_tests):
        relative_path = Path(path_to_test).relative_to(protoplaster_dir)
        link_path = (symlinks_dir / str(i))
        if not link_path.exists():
            link_path.symlink_to(protoplaster_dir, target_is_directory=True)
        link_to_test = link_path / relative_path
        links_to_test.append(link_to_test)
    return links_to_test


def extract_class_names(path):
    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    classes = [
        node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)
    ]
    return classes


def prepare_pytest_args(test_paths, args):
    pytest_args = f" --keep-duplicates -s -p no:cacheprovider -p protoplaster.conf.params_conf --yaml_file={args.test_file} "
    if args.output:
        pytest_args += f"--junitxml={args.output} "
    if args.artifacts_dir:
        pytest_args += f"--artifacts-dir={args.artifacts_dir} "
    links_to_tests = create_links_to_tests(test_paths)

    test_to_run = ""
    for test_path, link_to_test in zip(test_paths, links_to_tests):
        classes = extract_class_names(test_path)
        if len(classes) == 0:
            pr_warn(f"'{test_path}' has not class to test")
            continue
        test_class = classes[0]
        if len(classes) > 1:
            pr_warn(
                f"'{test_path}' has more that one class to test. Choosing first one: '{test_class}'"
            )
        test_to_run += f" {link_to_test}::{test_class}"
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

    try:
        response = requests.post(urljoin(base_url, "/api/v1/test-runs"),
                                 json=payload,
                                 timeout=REMOTE_RUN_TRIGGER_TIMEOUT)
        response.raise_for_status()
        run_data = response.json()
        print(
            f"[{machine}] Remote run triggered successfully. ID: {run_data.get('id')}"
        )
        return None
    except Exception as e:
        err_msg = f"[{machine}] Failed to trigger run: {e}"
        print(error(err_msg))
        return err_msg


def get_target_machines(args) -> Set:
    test_file = create_test_file(args)
    return test_file.get_all_machines()


def has_local_tests(args) -> bool:
    test_file = create_test_file(args)
    test_file.filter_runnable_tests(None)
    return len(test_file.tests) > 0


def run_tests(args):
    dispatched_remote_tests = False

    # Check execution context:
    # - <string>: Triggered by a `_trigger_remote_run` call from the orchestrator.
    #             Act as a DUT node, running ONLY the tests assigned to this specific node.
    # - None:     Act as the orchestrator, dispatching remote tests and running local ones.
    machine_target = getattr(args, "machine_target", None)
    if not machine_target:
        devices = {d['name']: d['url'] for d in get_all_devices()}
        for machine in get_target_machines(args):
            if machine in devices:
                _trigger_remote_run(machine, devices[machine], args)
                dispatched_remote_tests = True
            else:
                print(
                    error(f"Machine '{machine}' not defined in devices list"))

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

    if paths_to_tests == []:
        # If we dispatched remotes but have no local tests, that's fine.
        # If we have neither, it's a warning.
        if machine_target is None and dispatched_remote_tests:
            # No warning - we have dispatched tests
            pass
        else:
            print(warning("No tests to run on this device!"))

        return 0, []

    with test_file.merged_test_file() as tf:
        args.test_file = tf.name
        if args.generate_docs:
            generate_docs(
                OrderedDict.fromkeys(paths_to_tests).keys(),
                load_yaml(tf.name))
            sys.exit()

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

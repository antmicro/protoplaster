import ast
import os
import sys
import zipfile
from collections import OrderedDict
from pathlib import Path

import pytest
from jinja2 import Environment, DictLoader, select_autoescape

from protoplaster.docs.docs import TestDocs
from protoplaster.docs import __file__ as docs_path

from protoplaster.conf.csv_generator import CsvReportGenerator
from protoplaster.conf.parser import TestFile, load_yaml
from protoplaster.report_generators.test_report.protoplaster_test_report import generate_test_report
from protoplaster.report_generators.system_report.protoplaster_system_report import generate_system_report, CommandConfig, SubReportResult, run_command

TOP_LEVEL_TEMPLATE_PATH = "template.md"


def list_tests(args):
    test_file = TestFile(args.test_dir, args.test_file, args.custom_tests)
    if (group := args.group) is not (None or ""):
        test_file.filter_suite(group)

    for test in test_file.tests.keys():
        print(test)


def list_test_suites(args):
    test_file = TestFile(args.test_dir, args.test_file, args.custom_tests)
    if (group := args.group) is not (None or ""):
        test_file.filter_suite(group)

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


def prepare_pytest_args(tests, args):
    pytest_args = f" -s -p no:cacheprovider -p protoplaster.conf.params_conf --yaml_file={args.test_file} "
    if args.output:
        pytest_args += f"--junitxml={args.output} "
    if args.artifacts_dir:
        pytest_args += f"--artifacts-dir={args.artifacts_dir} "
    pytest_args = " ".join(tests) + pytest_args
    return pytest_args.strip().split(" ")


def generate_metadata(args, metadata_cmds):

    cmd_results = []
    for cmd in metadata_cmds.items():
        command_config = CommandConfig(cmd)
        result = run_command(command_config)
        cmd_results.append(result)
        with open(os.path.join(args.artifacts_dir, result.output_file),
                  "w") as f:
            f.write(result.raw_output)

    return cmd_results


def run_tests(args):
    test_file = TestFile(args.test_dir, args.test_file, args.custom_tests)
    if (group := args.group) is not (None or ""):
        test_file.filter_suite(group)

    test_modules = test_file.list_test_modules()
    metadata_cmds = test_file.list_metadata_commands()

    os.makedirs(args.artifacts_dir, exist_ok=True)

    if metadata_cmds:
        generate_metadata(args, metadata_cmds)

    if test_modules == []:
        print(warning("No tests to run!"))

    with test_file.merged_test_file() as tf:
        args.test_file = tf.name
        if args.generate_docs:
            generate_docs(
                OrderedDict.fromkeys(test_modules).keys(), load_yaml(tf.name))
            sys.exit()
        csv_report_gen = CsvReportGenerator(args.csv_columns)
        ret = pytest.main(prepare_pytest_args(test_modules, args),
                          plugins=[csv_report_gen])
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
    return ret

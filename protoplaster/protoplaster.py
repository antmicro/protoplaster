#!/usr/bin/env python3
import ast
import argparse
import os
import sys
import pytest
import yaml
from collections import OrderedDict
from colorama import init, Fore, Style
from jinja2 import Environment, DictLoader, select_autoescape
from pathlib import Path
import zipfile
import shutil

from protoplaster.docs.docs import TestDocs
from protoplaster.docs import __file__ as docs_path
from protoplaster.i2c.test import __file__ as i2c_test
from protoplaster.gpio.test import __file__ as gpio_test
from protoplaster.camera.test import __file__ as camera_test
from protoplaster.fpga.test import __file__ as fpga_test
from protoplaster.network.test import __file__ as network_test
from protoplaster.adc.adc.test import __file__ as adc_test
from protoplaster.adc.LTC2493.test import __file__ as LTC2493_test

from protoplaster.conf.csv_generator import CsvReportGenerator
from protoplaster.report_generators.test_report.protoplaster_test_report import generate_test_report
from protoplaster.report_generators.system_report.protoplaster_system_report import generate_system_report
from protoplaster.report_generators.system_report.protoplaster_system_report import __file__ as system_report_file

CONFIG_DIR = "/etc/protoplaster"
TOP_LEVEL_TEMPLATE_PATH = "template.md"

tests_paths = {
    "i2c": i2c_test,
    "gpio": gpio_test,
    "camera": camera_test,
    "fpga": fpga_test,
    "network": network_test,
    "adc": adc_test,
    "LTC2493": LTC2493_test,
}

init()


def warning(text):
    return Fore.YELLOW + f"[WARNING] {text}" + Style.RESET_ALL


def error(text):
    return Fore.RED + f"[ERROR] {text}" + Style.RESET_ALL


def info(text):
    return f"[INFO] {text}"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t",
                        "--test-file",
                        type=str,
                        default=f"{CONFIG_DIR}/test.yaml",
                        help="Path to the test yaml description")
    parser.add_argument("-g", "--group", type=str, help="Group to execute")
    parser.add_argument("--list-groups",
                        action="store_true",
                        help="List possible groups to execute")
    parser.add_argument("-o",
                        "--output",
                        type=str,
                        help="A junit-xml style report of the tests results")
    parser.add_argument("--csv",
                        type=str,
                        help="Generate a CSV report of the tests results")
    parser.add_argument(
        "--csv-columns",
        type=str,
        help="Comma-separated list of columns to be included in generated CSV")
    parser.add_argument("--generate-docs",
                        action="store_true",
                        help="Generate documentation")
    parser.add_argument("-c",
                        "--custom-tests",
                        type=str,
                        default=f"{CONFIG_DIR}/tests/*/",
                        help="Path to the custom tests sources")
    parser.add_argument("--report-output",
                        type=str,
                        help="Proplaster report archive")
    parser.add_argument(
        "--system-report-config",
        type=str,
        help="Path to the system report yaml config file",
        default=f"{os.path.dirname(system_report_file)}/default_commands.yml")
    parser.add_argument("--sudo", action='store_true', help="Run as sudo")
    args = parser.parse_args()
    if args.csv_columns and not args.csv and not args.report_output:
        parser.error("--csv-columns requires --csv or --report-output")
    return args


def parse_yaml(yaml_file):
    with open(yaml_file) as file:
        content = yaml.safe_load(file)
    return content


def get_list_of_tests(tests_dict):
    return tests_dict if isinstance(tests_dict, list) else [tests_dict]


def load_module(module_path, module_name):
    if not os.path.isfile(f"{module_path}/test.py"):
        print(
            warning(f'Additional module "{module_name}" could not be loaded!'))
        return False
    file_abs_path = os.path.abspath(module_path)
    tests_paths[module_name] = f"{file_abs_path}/test.py"
    sys.path.append(file_abs_path)
    print(
        info(
            f'Additional module loaded "{module_name}" at path {file_abs_path}'
        ))
    return True


def extract_tests(yaml_file, group, custom_path):
    content = parse_yaml(yaml_file)

    if group is not None and group in content:
        content = content[group]
    elif group is None:
        content = {
            mod_key: content[group_key][mod_key]
            for group_key in content
            for mod_key in content[group_key]
        }
    else:
        print(error(f'Group "{group}" not defined - Exiting!'))
        sys.exit(1)

    tests = []
    for module_name in content:
        if module_name in tests_paths:
            content[module_name] = get_list_of_tests(content[module_name])
        elif os.path.exists(f"{CONFIG_DIR}/{module_name}") and load_module(
                f"{CONFIG_DIR}/{module_name}", module_name):
            content[module_name] = get_list_of_tests(content[module_name])
        elif os.path.exists(f"{custom_path}") and load_module(
                f"{custom_path}", module_name):
            content[module_name] = get_list_of_tests(content[module_name])
        else:
            print(
                warning(f'Unknown module found: "{module_name}" - Skipping!'))
            continue
        tests += [tests_paths[module_name] for _ in content[module_name]]
    return tests


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
        class_macros = []
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
            class_macros.append(tests_class.name)

        functions = [
            f for f in ast.walk(tree)
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
                    error(f'Macro in the docstring for the "{func.name}" ' +
                          'function should have the same name as function ' +
                          '- Exiting!'))
                sys.exit(5)
            templates[func.name] = function_doc
            method_macros.append(func.name)

        # collect data from yaml file
        for test_group in yaml_content:
            for test_module in yaml_content[test_group]:
                module = test_path.split("/")
                if module[-2] == test_module:
                    module_details.append(
                        yaml_content[test_group][test_module])

        test_doc = TestDocs(class_macros, module_details, method_macros)
        tests_doc_list.append(test_doc)
    generate_rst_doc(tests_doc_list, templates)


def prepare_pytest_args(tests, args):
    pytest_args = f" -s -p no:cacheprovider -p protoplaster.conf.params_conf --yaml_file={args.test_file} "
    if args.output:
        pytest_args += f"--junitxml={args.output} "
    if args.group:
        pytest_args += f"--group={args.group} "
    pytest_args = " ".join(tests) + pytest_args
    return pytest_args.strip().split(" ")


def run_tests(args):
    tests = extract_tests(args.test_file, args.group, args.custom_tests)
    if tests == []:
        print(warning("No tests to run!"))
    if args.generate_docs:
        generate_docs(
            OrderedDict.fromkeys(tests).keys(), parse_yaml(args.test_file))
        sys.exit()
    csv_report_gen = CsvReportGenerator(args.csv_columns)
    pytest.main(prepare_pytest_args(tests, args), plugins=[csv_report_gen])
    if args.csv:
        with open(args.csv, "w") as csv_file:
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


def list_groups(yaml_file):
    content = parse_yaml(yaml_file)
    for group in content:
        print(group)


def main():
    args = parse_args()

    if args.sudo:
        os.execv(shutil.which("sudo"),
                 [__file__] + list(filter(lambda a: a != "--sudo", sys.argv)))
    if not os.path.exists(args.test_file):
        print(
            error(
                f"Test file {args.test_file} does not exist or you don't have sufficient permitions"
            ))
        exit(1)
    if args.list_groups:
        list_groups(args.test_file)
        sys.exit()
    run_tests(args)


if __name__ == "__main__":
    main()

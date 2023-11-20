#!/usr/bin/env python3
from jinja2 import Environment, DictLoader
import os
import sys


def get_name(interface_str):
    b = interface_str.find(":") + 2
    e = b + interface_str[b:].find(":")
    return interface_str[b:e]


def get(interface_str, property):
    b = interface_str.find(property) + len(property) + 1
    e = b + interface_str[b:].find(" ")
    return interface_str[b:e]


if __name__ == "__main__":

    if len(sys.argv) < 2:
        sys.exit(1)

    raw_interfaces = []
    interfaces = []

    curr_b = 0
    for i in range(len(sys.argv[1]) - 2):
        if sys.argv[1][i + 1] != " " and sys.argv[1][i] == "\n":
            raw_interfaces.append(sys.argv[1][curr_b:i])
            curr_b = i + 1
    raw_interfaces.append(sys.argv[1][curr_b:-1])

    for interface_str in raw_interfaces:
        interfaces.append(
            (get_name(interface_str), get(interface_str, "state"),
             get(interface_str, "inet"), get(interface_str, "inet6")))

    with open(f"{os.path.dirname(__file__)}/generic_table_template.html"
              ) as template_file:
        html_template = template_file.read()
    environment = Environment(
        loader=DictLoader({"report_template": html_template}))
    template = environment.get_template("report_template")
    print(
        template.render(fields=["interface", "state", "ipv4", "ipv6"],
                        rows=interfaces))

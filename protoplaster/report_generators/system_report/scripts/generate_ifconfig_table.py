#!/usr/bin/env python3
from jinja2 import Environment, DictLoader
import os
import sys
import ipaddress


def get_name(interface_str):
    return interface_str[0:interface_str.find(":")]


def get_state(interface_str):
    b = interface_str.find("<")
    e = interface_str.find(">")
    is_running = interface_str[b:e].find("RUNNING") != -1
    return "UP" if is_running else "DOWN"


def get(interface_str, property):
    b = interface_str.find(property) + len(property) + 1
    e = b + interface_str[b:].find(" ")
    return interface_str[b:e]


def get_ipv4(interace_str):
    return get(interace_str, "inet") + "/" + str(
        ipaddress.IPv4Network(
            (0, get(interface_str, "netmask").strip())).prefixlen)


def get_ipv6(interace_str):
    return get(interace_str, "inet6") + "/" + get(interface_str, "prefixlen")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        sys.exit(1)

    raw_interfaces = []
    interfaces = []

    curr_b = 0
    for i in range(len(sys.argv[1]) - 2):
        if sys.argv[1][i + 1] != " " and sys.argv[1][
                i + 1] != "\n" and sys.argv[1][i] == "\n":
            raw_interfaces.append(sys.argv[1][curr_b:i])
            curr_b = i + 1
    raw_interfaces.append(sys.argv[1][curr_b:-1])

    for interface_str in raw_interfaces:
        interfaces.append((get_name(interface_str), get_state(interface_str),
                           get_ipv4(interface_str), get_ipv6(interface_str)))

    with open(f"{os.path.dirname(__file__)}/generic_table_template.html"
              ) as template_file:
        html_template = template_file.read()
    environment = Environment(
        loader=DictLoader({"report_template": html_template}))
    template = environment.get_template("report_template")
    print(
        template.render(fields=["interface", "state", "ipv4", "ipv6"],
                        rows=interfaces))

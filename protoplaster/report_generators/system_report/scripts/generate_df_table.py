#!/usr/bin/env python3
from jinja2 import Environment, DictLoader
import os
import sys

if __name__ == "__main__":

    if len(sys.argv) < 2:
        sys.exit(1)

    rows = sys.argv[1].splitlines()
    if len(rows) < 2:
        sys.exit(0)
    rows = [row.split() for row in rows]
    rows[0][len(rows[0]) - 2] = rows[0][len(rows[0]) - 2] + " " + rows[0][len(
        rows[0]) - 1]  #last column (Mounted on) have space in it
    rows[0].pop(len(rows[0]) - 1)

    with open(f"{os.path.dirname(__file__)}/generic_table_template.html"
              ) as template_file:
        html_template = template_file.read()
    environment = Environment(
        loader=DictLoader({"report_template": html_template}))
    template = environment.get_template("report_template")
    print(template.render(fields=rows[0], rows=rows[1:]))

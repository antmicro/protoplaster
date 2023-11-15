#!/usr/bin/env python3
import argparse
import csv
import os
from jinja2 import Environment, FileSystemLoader


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i",
                        "--input-file",
                        type=str,
                        help="Path to the csv file")
    parser.add_argument("-t",
                        "--type",
                        type=str,
                        choices=["md", "html"],
                        required=True,
                        help="Output type")
    parser.add_argument("-o",
                        "--output-file",
                        type=str,
                        help="Path to the output file")
    return parser.parse_known_args()


def human_readable_time(seconds):
    units = [("h", 3600), ("m", 60), ("s", 1), ("ms", 0.001), ("us", 0.000001)]
    t = []
    for unit, div in units:
        val = seconds // div
        if val >= 1:
            t.append(f"{val:g}{unit}")
            seconds -= val * div
        if len(t) == 2:
            break
    return " ".join(t)


custom_columns_md = {
    "status": (lambda value: f"<span style='color:green'>{value}"
               if value == "passed" else f"<span style='color:red'>{value}"),
    "duration": (lambda value: human_readable_time(float(value)))
}

custom_columns_html = {
    "status": (lambda value: (value, "status-passed"
                              if value == "passed" else "status-failed")),
    "duration": (lambda value: (human_readable_time(float(value)), ""))
}


def main():
    args, unnamed = parse_args()

    if not args.input_file and len(unnamed) == 0:
        print("missing input name arg")
        return 1

    input_file = args.input_file if args.input_file else unnamed[0]
    output_file = args.output_file if args.output_file else input_file.split(
        ".")[0] + "." + args.type
    custom_columns = custom_columns_md if args.type == "md" else custom_columns_html

    with open(input_file) as csv_file:
        reader = csv.DictReader(csv_file)
        environment = Environment(
            loader=FileSystemLoader(os.path.dirname(__file__)))
        template = environment.get_template(
            f"report_table_template.{args.type}")
        with open(output_file, "w") as file:
            file.write(
                template.render(fields=reader.fieldnames,
                                reader=reader,
                                custom_columns=custom_columns))


if __name__ == "__main__":
    main()

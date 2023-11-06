#!/usr/bin/env python3
import argparse
import csv
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i",
                        "--input-file",
                        type=str,
                        help="Path to the csv file")
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


custom_columns = {
    "status":
    (lambda value:
     f"<td class='{'status-passed' if value == 'passed' else 'status-failed'}'>{value}</td>"
     ),
    "duration": (lambda value: f"<td>{human_readable_time(float(value))}</td>")
}


def main():
    args, rest = parse_args()

    if not args.input_file and len(rest) == 0:
        print("missing input name arg")
        return

    input_file = args.input_file if args.input_file else rest[0]
    output_file = args.output_file if args.output_file else input_file.split(
        ".")[0] + ".html"

    with open(input_file) as csv_file:
        with open(output_file, "w") as html_file:
            reader = csv.DictReader(csv_file)

            html_file.write("<html><head><style>")
            with open(f"{os.path.dirname(__file__)}/style.css") as style:
                html_file.write(style.read())
            html_file.write(
                "</style></head><body><table style='report-table'>")

            html_file.write("<tr>")
            for field in reader.fieldnames:
                html_file.write(f"<th>{field}</th>")
            html_file.write("</tr>")

            for row in reader:
                html_file.write("<tr>")
                for field in reader.fieldnames:
                    if field not in custom_columns:
                        html_file.write(f"<td>{row[field]}</td>")
                    else:
                        html_file.write(custom_columns[field](row[field]))
                html_file.write("</tr>")

            html_file.write("</table></body></html>")


if __name__ == "__main__":
    main()

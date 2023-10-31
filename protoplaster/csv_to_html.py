#!/usr/bin/env python3
import argparse
import csv


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i",
                        "--input-file",
                        required=True,
                        type=str,
                        help="Path to the csv file")
    parser.add_argument("-o",
                        "--output-file",
                        required=True,
                        type=str,
                        help="Path to the output file")
    return parser.parse_args()


def main():
    args = parse_args()

    with open(args.input_file) as csv_file:
        with open(args.output_file, "w") as html_file:
            reader = csv.DictReader(csv_file)

            html_file.write("<table>")

            html_file.write("<tr>")
            for field in reader.fieldnames:
                html_file.write(f"<th>{field}</th>")
            html_file.write("</tr>")

            for row in reader:
                html_file.write("<tr>")
                for field in reader.fieldnames:
                    html_file.write(f"<td>{row[field]}</td>")
                html_file.write("</tr>")

            html_file.write("</table>")


if __name__ == "__main__":
    main()

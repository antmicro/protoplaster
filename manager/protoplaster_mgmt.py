#!/usr/bin/env python3

import argparse
import os
import requests
import sys
import traceback
import yaml

import manager.configs
import manager.runs


def main():
    parser = argparse.ArgumentParser(
        description="Tool for managing Protoplaster via remote API", )

    parser.add_argument(
        "--url",
        default="http://127.0.0.1:5000/",
        help=
        "URL to a device running Protoplaster server (default: http://127.0.0.1:5000/)",
    )
    parser.add_argument(
        "--config",
        help=
        "Config file with values for url, config-dir, report-dir, artifact-dir",
    )
    parser.add_argument(
        "--config-dir",
        default="./",
        metavar="CONFIG_DIR",
        help="Directory to save fetched config (default: ./)",
    )
    parser.add_argument(
        "--report-dir",
        default="./",
        help="Directory to save a test report (default: ./)",
    )
    parser.add_argument(
        "--artifact-dir",
        default="./",
        help="Directory to save a test artifact (default: ./)",
    )

    subparsers = parser.add_subparsers(required=True,
                                       title="available commands")

    # Add all subparsers for the different subcommands
    manager.configs.add_configs_parser(subparsers)
    manager.runs.add_runs_parser(subparsers)
    # Wrap argv so when no arguments are passed, we inject a help screen
    wrapped_args = None if sys.argv[1:] else ["--help"]

    args = parser.parse_args(args=wrapped_args)

    config = {}
    if args.config is not None:
        try:
            with open(args.config) as file:
                config = yaml.safe_load(file)
        except Exception as e:
            print(f"Failed to read config: {e}")
            exit(1)

    url = config.get("url", args.url)
    config_dir = config.get("config-dir", args.config_dir)
    report_dir = config.get("report-dir", args.report_dir)
    artifact_dir = config.get("artifact-dir", args.artifact_dir)

    try:
        ret = args.func(args)
        if ret is not None:
            print("protoplaster-mgmt:", ret)
            exit(1)
    except requests.ConnectionError as e:
        print("protoplaster-mgmt: Connection to the server failed:", e)
        exit(1)
    except requests.Timeout as e:
        print("protoplaster-mgmt: Server request timed out:", e)
        exit(1)
    except RuntimeError as e:
        print("protoplaster-mgmt:", e)
        exit(1)
    except Exception:
        traceback.print_exc()
        print("protoplaster-mgmt: Unhandled exception!")
        exit(1)


if __name__ == "__main__":
    main()

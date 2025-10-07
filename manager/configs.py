import argparse
import json
import os.path
import requests
from pathlib import Path

StrPath = str | Path


def check_status(response: requests.models.Response):
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.json()['error']}")
        return True
    return False


def configs_list(args):
    r = requests.get(f"{args.url}/api/v1/configs")
    if check_status(r):
        return
    print(f"Available configs:")
    print(json.dumps(r.json(), indent=4))


def config_upload(args):
    try:
        files = {'file': open(args.path, 'rb')}
    except Exception as e:
        print(f"Failed to open the config to upload: {str(e)}")
        return
    r = requests.post(f"{args.url}/api/v1/configs", files=files)
    if check_status(r):
        return
    print(f"Uploaded `{args.path}`")


def config_info(args):
    r = requests.get(f"{args.url}/api/v1/configs/{args.name}")
    if check_status(r):
        return
    print(f"Config info fetched from the server:")
    print(json.dumps(r.json(), indent=4))


def config_fetch(args):
    r = requests.get(f"{args.url}/api/v1/configs/{args.name}/file")
    if check_status(r):
        return
    save_path = os.path.join(args.config_dir, args.name)
    try:
        with open(save_path, "wb") as file:
            file.write(r.content)
        print(f"Config written to {save_path}")
    except Exception as e:
        print(f"Failed to save the config: {str(e)}")


def config_delete(args):
    r = requests.delete(f"{args.url}/api/v1/configs/{args.name}")
    if check_status(r):
        return
    print(f"Config '{args.name}' deleted")


def add_configs_parser(parser: argparse._SubParsersAction):
    configs = parser.add_parser("configs", help="Configs management")
    sub = configs.add_subparsers(required=True, title="Configs commands")

    list = sub.add_parser("list", help="List available test configs")
    list.set_defaults(func=configs_list)

    upload = sub.add_parser("upload", help="Upload a test config")
    upload.set_defaults(func=config_upload)
    upload.add_argument("--path",
                        type=str,
                        required=True,
                        help="Path to a test config file")

    info = sub.add_parser("info", help="Information about a test config")
    info.set_defaults(func=config_info)
    info.add_argument("--name",
                      type=str,
                      required=True,
                      help="Test config name")

    fetch = sub.add_parser("fetch", help="Fetch a test config file")
    fetch.set_defaults(func=config_fetch)
    fetch.add_argument("--name",
                       type=str,
                       required=True,
                       help="Test config name")

    delete = sub.add_parser("delete", help="Delete a test config file")
    delete.set_defaults(func=config_delete)
    delete.add_argument("--name",
                        type=str,
                        required=True,
                        help="Test config name")

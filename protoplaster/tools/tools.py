import requests
from colorama import Fore, Style
from typing import Callable, Optional, List, Any

from protoplaster.webui.devices import get_device_by_name


def assert_user_input(user_message,
                      assertion_message="User input failed",
                      possible_answers=["y", "n"],
                      correct_answer=0):
    answer = input(
        f"{user_message} [{'/'.join([ans.upper() if i == correct_answer else ans for i, ans in enumerate(possible_answers)])}] "
    )
    if answer != "":
        assert answer.lower() == possible_answers[correct_answer].lower()


def warning(text):
    return Fore.YELLOW + f"[WARNING] {text}" + Style.RESET_ALL


def pr_warn(text):
    print(warning(text))


def error(text):
    return Fore.RED + f"[ERROR] {text}" + Style.RESET_ALL


def pr_err(text):
    print(error(text))


def info(text):
    return f"[INFO] {text}"


def pr_info(text):
    print(info(text))


def trigger_on_remote(target: str,
                      method: Callable,
                      args: Optional[List[Any]] = None) -> Optional[Any]:
    """
    Executes a function on a remote node via RPC.

    - target (str): The name of the target device (e.g., 'node1') as registered in the device manager.
    - method (Callable): The actual function object to execute on the remote node. The function must be defined in a module accessible to the remote agent.
    - args (list, optional): A list of positional arguments to pass to the remote function. Defaults to None.

    Returns: (Any) The return value of the executed function if successful; otherwise, None.
    """
    device = get_device_by_name(target)
    if not device:
        print(error(f"Device {target} not found"))
        return None

    url = device["url"]

    try:
        requests.get(url, timeout=5)
    except requests.exceptions.RequestException:
        raise Exception(f"Device {target} is offline")

    payload = {
        "module": method.__module__,
        "function": method.__name__,
        "args": args or [],
    }

    try:
        resp = requests.post(f"{url}/api/v1/exec", json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise Exception(data["error"])
        return data["result"]
    except Exception as e:
        print(error(f"Failed to execute on {target}: {e}"))
        return None

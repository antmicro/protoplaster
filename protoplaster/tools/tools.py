import requests
from colorama import Fore, Style
from typing import Callable, Optional, List, Any, Union
from concurrent.futures import ThreadPoolExecutor, Future

from protoplaster.webui.devices import get_device_by_name

# Executor to manage threads for non-blocking `trigger_on_remote` calls
_executor = ThreadPoolExecutor()


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


def _execute_request(url: str, method: Callable, args: List[Any]) -> Any:
    payload = {
        "module": method.__module__,
        "function": method.__name__,
        "args": args,
    }

    resp = requests.post(f"{url}/api/v1/exec", json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise Exception(data["error"])
    return data["result"]


def trigger_on_remote(
        target: str,
        method: Callable,
        args: Optional[List[Any]] = None,
        non_blocking: bool = False) -> Union[Optional[Any], Future]:
    """
    Executes a function on a remote node via RPC.

    - target (str): The name of the target device (e.g., 'node1') as registered in the device manager.
    - method (Callable): The actual function object to execute on the remote node. The function must be defined in a module accessible to the remote agent.
    - args (list, optional): A list of positional arguments to pass to the remote function. Defaults to None.
    - non_blocking (bool, optional): If True, returns a Future object immediately. Defaults to False.

    Returns:
        - If non_blocking=False: The return value of the executed function (or None on failure).
        - If non_blocking=True: A `concurrent.futures.Future` object representing the execution.
    """
    args = args or []
    device = get_device_by_name(target)
    if not device:
        print(error(f"Device {target} not found"))
        return None

    url = device["url"]

    try:
        requests.get(url, timeout=5)
    except requests.exceptions.RequestException:
        raise Exception(f"Device {target} is offline")

    if non_blocking:
        return _executor.submit(_execute_request, url, method, args)
    else:
        return _execute_request(url, method, args)

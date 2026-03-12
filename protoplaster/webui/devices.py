from protoplaster.conf.consts import LOCAL_DEVICE_NAME
from protoplaster.tools.log import error
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Optional, List, Any, Union
import requests

_devices = []


def get_all_devices():
    return list(_devices)


def get_remote_devices():
    return [d for d in _devices if d["name"] != LOCAL_DEVICE_NAME]


def get_device_by_name(device_name):
    return next((d for d in _devices if d["name"] == device_name), None)


def add_device(name, url, is_broadcast=False):

    # Check for missing scheme manually first. We do this string check because
    # `urlparse` gets confused by "host:port". If "://" is missing, we force http.
    if "://" not in url:
        url = f"http://{url}"

    parsed = urlparse(url)
    if parsed.port is None:
        parsed = parsed._replace(netloc=f"{parsed.netloc}:5000")

    url = urlunparse(parsed)

    if any(d["name"] == name for d in _devices):
        raise ValueError(f"Device '{name}' already exists")
    if any(d["url"] == url for d in _devices):
        raise ValueError(f"Device with URL '{url}' already exists")
    device = {"name": name, "url": url}
    _devices.append(device)
    if not is_broadcast:
        for d in get_remote_devices()[:-1]:
            # Tell other devices about this device
            trigger_on_remote(d["name"], add_device, [name, url, True])
            # And this device about other devices
            trigger_on_remote(name, add_device, [d["name"], d["url"], True])
    return device


def remove_device(device_name, is_broadcast=False):
    global _devices
    if device_name == LOCAL_DEVICE_NAME:
        raise ValueError("Cannot remove the local device")
    before = len(_devices)
    _devices = [d for d in _devices if d["name"] != device_name]
    if not is_broadcast:
        for d in get_remote_devices():
            trigger_on_remote(d["name"], remove_device, [device_name, True])
    return len(_devices) < before


# Executor to manage threads for non-blocking `trigger_on_remote` calls
_executor = ThreadPoolExecutor()


def _execute_request(url: str, method: Callable, args: List[Any]) -> Any:
    payload = {
        "module": method.__module__,
        "function": method.__name__,
        "args": args,
    }

    resp = requests.post(f"{url}/api/v1/exec", json=payload, timeout=60)
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

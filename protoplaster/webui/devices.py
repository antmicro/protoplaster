from protoplaster.conf.consts import LOCAL_DEVICE_NAME
from urllib.parse import urlparse, urlunparse

_devices = []


def get_all_devices():
    return list(_devices)


def get_device_by_name(device_name):
    return next((d for d in _devices if d["name"] == device_name), None)


def add_device(name, url):

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
    return device


def remove_device(device_name):
    global _devices
    if device_name == LOCAL_DEVICE_NAME:
        raise ValueError("Cannot remove the local device")
    before = len(_devices)
    _devices = [d for d in _devices if d["name"] != device_name]
    return len(_devices) < before

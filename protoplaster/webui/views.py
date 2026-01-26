from flask import render_template, request, redirect, url_for, flash, jsonify
from . import webui_blueprint
import requests
from protoplaster.webui.devices import get_all_devices, get_device_by_name, add_device, remove_device
from protoplaster.conf.consts import WEBUI_POLLING_INTERVAL
from protoplaster.tools.tools import error


@webui_blueprint.route("/")
def index():
    return redirect(url_for("webui.devices"))


@webui_blueprint.route("/devices")
def devices():
    """List all known devices."""
    devices = get_all_devices()
    for d in devices:
        try:
            requests.get(f"{d['url']}/api/v1/test-runs", timeout=0.5)
            d['online'] = True
        except requests.exceptions.RequestException:
            d['online'] = False

    return render_template("devices.html",
                           devices=devices,
                           active="devices",
                           polling_interval=WEBUI_POLLING_INTERVAL,
                           disable_nav=False)


@webui_blueprint.route("/devices/status")
def devices_status():
    """Return status of all devices."""
    devices = get_all_devices()
    status = {}
    for d in devices:
        try:
            requests.get(f"{d['url']}/api/v1/test-runs", timeout=0.5)
            is_online = True
        except requests.exceptions.RequestException:
            is_online = False
        status[d['name']] = is_online
    return jsonify(status)


@webui_blueprint.route("/devices/add", methods=["POST"])
def add_device_route():
    """Add a new remote device."""
    name = request.form.get("name")
    url = request.form.get("url")

    try:
        add_device(name, url)
    except ValueError as e:
        flash(str(e), "danger")
    return redirect(url_for("webui.devices"))


@webui_blueprint.route("/devices/remove/<device_name>", methods=["POST"])
def remove_device_route(device_name):
    """Remove a device."""
    remove_device(device_name)
    return redirect(url_for("webui.devices"))


@webui_blueprint.route("/configs")
def configs():
    devices = get_all_devices()
    for d in devices:
        try:
            r = requests.get(f"{d['url']}/api/v1/configs", timeout=2)
            d['configs'] = r.json()
        except Exception as e:
            print(error(f"Failed to fetch configs for {d['url']}: {e}"))
            d['configs'] = None

    return render_template("configs.html",
                           devices=devices,
                           active="configs",
                           polling_interval=WEBUI_POLLING_INTERVAL,
                           disable_nav=False)


@webui_blueprint.route("/runs")
def test_runs():
    devices = get_all_devices()
    for d in devices:
        try:
            d['runs'] = requests.get(f"{d['url']}/api/v1/test-runs",
                                     timeout=1).json()
        except Exception as e:
            print(error(f"Failed to fetch runs for {d['url']}: {e}"))
            d['runs'] = None

    return render_template("runs.html",
                           devices=devices,
                           active="runs",
                           polling_interval=WEBUI_POLLING_INTERVAL,
                           disable_nav=False)

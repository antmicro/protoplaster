from flask import render_template, request, redirect, url_for, flash
from . import webui_blueprint
import requests
from protoplaster.webui.devices import get_all_devices, get_device_by_name, add_device, remove_device
from protoplaster.conf.consts import WEBUI_POLLING_INTERVAL


@webui_blueprint.route("/")
def index():
    return redirect(url_for("webui.devices"))


@webui_blueprint.route("/devices")
def devices():
    """List all known devices."""
    devices = get_all_devices()
    return render_template("devices.html", devices=devices, active="devices")


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
    device_name = request.args.get("device")
    devices = get_all_devices()
    selected_device = get_device_by_name(device_name) or devices[0]
    r = requests.get(f"{selected_device['url']}/api/v1/configs", timeout=2)
    configs = r.json()
    return render_template("configs.html",
                           configs=configs,
                           devices=devices,
                           selected_device=selected_device,
                           active="configs")


@webui_blueprint.route("/runs")
def test_runs():
    device_name = request.args.get("device")
    devices = get_all_devices()
    selected_device = get_device_by_name(device_name) or devices[0]
    r = requests.get(f"{selected_device['url']}/api/v1/test-runs", timeout=2)
    runs = r.json()
    return render_template("runs.html",
                           runs=runs,
                           devices=devices,
                           selected_device=selected_device,
                           active="runs",
                           polling_interval=WEBUI_POLLING_INTERVAL)

from flask import Blueprint, jsonify
from protoplaster.webui.devices import get_all_devices

devices_blueprint: Blueprint = Blueprint("protoplaster-devices", __name__)


@devices_blueprint.route("/api/v1/devices")
def fetch_devices():
    """Fetch a list of devices

    :status 200: no error

    :>jsonarr string name: device name
    :>jsonarr string url: device url

    **Example Request**

    .. sourcecode:: http

        GET /api/v1/devices HTTP/1.1
        Accept: application/json, text/javascript


    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
          {
            "name": "device1",
            "url": "http://192.168.1.100:5000"
          }
        ]
    """
    return jsonify(get_all_devices())
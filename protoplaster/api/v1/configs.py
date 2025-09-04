from flask import Blueprint, current_app, jsonify, request, send_from_directory
import os
from datetime import datetime, timezone
from werkzeug.utils import secure_filename

configs_blueprint: Blueprint = Blueprint("protoplaster-configs", __name__)


def file_to_config_entry(config_dir: str, filename: str):
    path = os.path.join(config_dir, filename)

    mtime = os.path.getmtime(path)
    created = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()

    return {
        "name": filename,
        "created": created,
    }


@configs_blueprint.route("/api/v1/configs")
def fetch_configs():
    """Fetch a list of configs

    :status 200: no error

    :>jsonarr string created: UTC datetime of config upload (RFC822)
    :>jsonarr string name: config name

    **Example Request**

    .. sourcecode:: http

        GET /api/v1/configs HTTP/1.1
        Accept: application/json, text/javascript


    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
          {
            "name": "sample_config.yaml",
            "created": "Mon, 25 Aug 2025 16:58:35 +0200",
          }
        ]
    """  # noqa: E501

    config_dir = current_app.config["CONFIG_DIR"]
    if not config_dir:
        return jsonify({"error": "CONFIG_DIR not configured"}), 500

    try:
        filenames = [
            f for f in os.listdir(config_dir)
            if os.path.isfile(os.path.join(config_dir, f))
        ]
    except FileNotFoundError:
        return jsonify({"error": f"Directory not found: {config_dir}"}), 404

    configs = [file_to_config_entry(config_dir, f) for f in filenames]

    return jsonify(configs)


@configs_blueprint.route("/api/v1/configs", methods=["POST"])
def upload_config():
    """Upload a test config

    :form file: yaml file with the test config

    :status 200: no error, config was uploaded
    :status 400: file was not provided

    **Example Request**

    .. sourcecode:: http

        POST /api/v1/configs HTTP/1.1
        Accept: */*
        Content-Length: 4194738
        Content-Type: multipart/form-data; boundary=------------------------0f8f9642db3a513e

        --------------------------0f8f9642db3a513e
        Content-Disposition: form-data; name="file"; filename="config.yaml"
        Content-Type: application/octet-stream

        <file contents>
        --------------------------0f8f9642db3a513e--


    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
    """  # noqa: E501
    config_dir = current_app.config.get("CONFIG_DIR")
    if not config_dir:
        return jsonify({"error": "CONFIG_DIR not configured"}), 500

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    filename = secure_filename(file.filename)
    save_path = os.path.join(config_dir, filename)
    try:
        file.save(save_path)
    except Exception as e:
        return jsonify({"error": f"Failed to save file: {str(e)}"}), 500

    return jsonify(file_to_config_entry(config_dir, filename))


@configs_blueprint.route("/api/v1/configs/<string:config_name>")
def fetch_one_config(config_name: str):
    """Fetch information about a config

    :status 200: no error
    :status 404: config does not exist

    :>json string created: UTC datetime of config upload (RFC822)
    :>json string config_name: config name

    **Example Request**

    .. sourcecode:: http

        GET /api/v1/configs/sample_config.yaml HTTP/1.1
        Accept: application/json, text/javascript

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "name": "sample_config.yaml",
          "created": "Mon, 25 Aug 2025 16:58:35 +0200",
        }
    """  # noqa: E501
    config_dir = current_app.config["CONFIG_DIR"]
    if not config_dir:
        return jsonify({"error": "CONFIG_DIR not configured"}), 500

    if not os.path.exists(os.path.join(config_dir, config_name)):
        return jsonify({"error": f"File not found: {config_name}"}), 404

    config = file_to_config_entry(config_dir, config_name)

    return jsonify(config)


@configs_blueprint.route("/api/v1/configs/<string:config_name>/file")
def fetch_config_file(config_name: str):
    """Fetch a config file

    :status 200: no error
    :status 404: config does not exist

    :>file text/yaml: YAML config file

    **Example Request**

    .. sourcecode:: http

        GET /api/v1/configs/sample_config.yaml/file HTTP/1.1

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: text/yaml
        Content-Disposition: attachment; filename="sample_config.yaml"

        base:
          network:
            - interface: enp14s0
    """  # noqa: E501
    config_dir = current_app.config["CONFIG_DIR"]
    config_file = os.path.join(config_dir, config_name)

    if not os.path.isfile(config_file):
        return jsonify({"error": "Configuration file not found"}), 404

    return send_from_directory(os.path.abspath(config_dir),
                               config_name,
                               as_attachment=True,
                               mimetype="text/yaml")


@configs_blueprint.route("/api/v1/configs/<string:config_name>",
                         methods=["DELETE"])
def delete_config(config_name: str):
    """Remove a test config

    :param name: filename of the test config

    :status 200: no error, config was removed
    :status 404: file was not found

    **Example Request**

    .. sourcecode:: http

        DELETE /api/v1/configs/sample_config.yaml HTTP/1.1

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
    """  # noqa: E501
    config_dir = current_app.config["CONFIG_DIR"]
    config_path = os.path.join(config_dir, config_name)

    if not os.path.isfile(config_path):
        return jsonify({"error": "Configuration file not found"}), 404

    os.remove(config_path)
    return {}

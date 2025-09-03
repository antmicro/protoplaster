from flask import Blueprint

configs_blueprint: Blueprint = Blueprint("protoplaster-configs", __name__)


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
    #TODO: Add implementation
    return {}, 200


@configs_blueprint.route("/api/v1/configs", methods=["POST"])
def upload_config(scopes: list[str] = []):
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
    #TODO: Add implementation
    return {}, 200


@configs_blueprint.route("/api/v1/configs/<string:config_name>")
def fetch_one_config():
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
    #TODO: Add implementation
    return {}, 200


@configs_blueprint.route("/api/v1/configs/<string:config_name>/file")
def fetch_config_file():
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
    #TODO: Add implementation
    return {}, 200


@configs_blueprint.route("/api/v1/configs/<string:name>", methods=["DELETE"])
def delete_config(scopes: list[str] = []):
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
    #TODO: Add implementation
    return {}, 200

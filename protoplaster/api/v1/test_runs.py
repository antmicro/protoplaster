from flask import Blueprint

test_runs_blueprint: Blueprint = Blueprint("protoplaster-test-runs", __name__)


@test_runs_blueprint.route("/api/v1/test-runs")
def fetch_test_runs():
    """Fetch a list of test runs

    :status 200: no error

    :>jsonarr integer run_id: run id
    :>jsonarr string config_name: name of config for this test run
    :>jsonarr string test_suite_name: name of the test suite for this test run
    :>jsonarr string created: UTC datetime of test run start (RFC822)
    :>jsonarr string completed: UTC completion time (RFC822) 
    :>jsonarr string status: test run status, one of:
        * pending   - accepted but not started
        * running   - currently executing
        * finished  - completed successfully
        * failed    - error during execution
        * aborted   - stopped by user or system
    :>jsonarr dict[str, str] metadata: optional test run metadata (key/value pairs)

    **Example Request**

    .. sourcecode:: http

        GET /api/v1/test-runs HTTP/1.1
        Accept: application/json, text/javascript


    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        [
          {
            "run_id": 1,
            "config_name": "config1.yaml"
            "test_suite_name": "simple-test"
            "status": "finished",
            "created": "Mon, 25 Aug 2025 15:56:35 +0200",
            "metadata": {
              "bsp-sha256": "a5603553e0eaad133719dc19b57c96e811a72af5329e120310f96b4fdc891732"
            }
          },
          {
            "run_id": 2,
            "config_name": "config2.yaml"
            "test_suite_name": "complex-test"
            "status": "running",
            "created": "Mon, 25 Aug 2025 16:58:35 +0200",
            "metadata": {}
          }
        ]
    """  # noqa: E501
    #TODO: Add implementation
    return {}, 200


@test_runs_blueprint.route("/api/v1/test-runs", methods=["POST"])
def trigger_test_run(scopes: list[str] = []):
    """Trigger a test run


    :status 200: no error, test run was triggered
    :status 400: file was not provided

    :<json string config_name: name of config for this test run
    :<json string test_suite_name: name of the test suite for this test run

    **Example Request**

    .. sourcecode:: http

        POST /api/v1/test-runs/ HTTP/1.1
        Content-Type: application/json
        Accept: application/json, text/javascript

        {
          "config_name": "config1.yaml",
          "test_suite_name": "simple-test"
        }

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
    """  # noqa: E501
    #TODO: Add implementation
    return {}, 200


@test_runs_blueprint.route("/api/v1/test-runs/<int:identifier>")
def fetch_one_test_run(identifier: int):
    """Fetch information about a test run

    :param identifier: test run identifier
    :status 200: no error
    :status 404: test run does not exist

    :>json integer id: test run identifier
    :>json string created: UTC creation time (RFC822)
    :>json string completed: UTC completion time (RFC822)
    :>json string status: test run status, one of:
        * pending   - accepted but not started
        * running   - currently executing
        * finished  - completed successfully
        * failed    - error during execution
        * aborted   - stopped by user or system
    :>json dict[str, str] metadata: optional test run metadata (key/value pairs)

    **Example Request**

    .. sourcecode:: http

        GET /api/v1/test-runs/1 HTTP/1.1

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "run_id": 1,
          "config_name": "config1.yaml"
          "status": "finished",
          "created": "Mon, 25 Aug 2025 15:56:35 +0200",
          "metadata": {
            "bsp-sha256": "a5603553e0eaad133719dc19b57c96e811a72af5329e120310f96b4fdc891732"
          }
        }
    """  # noqa: E501
    #TODO: Add implementation
    return {}, 200


@test_runs_blueprint.route("/api/v1/test-runs/<int:identifier>",
                           methods=["DELETE"])
def delete_test_run(identifier: int):
    """Cancel a test run

    :param identifier: test run identifier
    :status 200: no error
    :status 400: test run not in progress
    :status 404: test run does not exist

    **Example Request**

    .. sourcecode:: http

        DELETE /api/v1/test-runs/1 HTTP/1.1

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
    """  # noqa: E501
    #TODO: Add implementation
    return {}, 200


@test_runs_blueprint.route("/api/v1/test-runs/<int:identifier>/report")
def fetch_test_run_report(identifier: int):
    """Fetch test run report

    :param identifier: test run identifier
    :status 200: no error
    :status 404: test run not completed or does not exist

    :>file text/csv: CSV file containing the full test report

    **Example request**

        GET /api/v1/runs/1/report HTTP/1.1

    **Example response**

        HTTP/1.1 200 OK
        Content-Type: text/csv
        Content-Disposition: attachment; filename="report-run-12345.csv"

        device name,test name,module,duration,message,status
        enp14s0,exist,test.py::TestNetwork::test_exist,0.0007359918672591448,,passed

    """  # noqa: E501
    #TODO: Add implementation
    return {}, 200

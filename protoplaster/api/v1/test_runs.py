from flask import Blueprint

test_runs_blueprint: Blueprint = Blueprint("protoplaster-test-runs", __name__)


@test_runs_blueprint.route("/api/v1/test-runs")
def fetch_test_runs():
    """Fetch a list of test runs

    :status 200: no error

    :>jsonarr integer run_id: run id
    :>jsonarr string config_name: name of config for this test run
    :>jsonarr string test_suite_name: name of the test suite for this test run
    :>jsonarr string created_at: UTC datetime of test run creation (RFC822)
    :>jsonarr string started_at: UTC datetime of test run start (RFC822)
    :>jsonarr string finished_at: UTC completion time (RFC822)
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
            "run_id": "25d9f4a2-2556-4647-b3cc-762348dc51ce",
            "config_name": "config1.yaml"
            "test_suite_name": "simple-test"
            "status": "finished",
            "created_at": "Mon, 25 Aug 2025 15:56:35 +0200",
            "started_at": "Mon, 25 Aug 2025 15:56:36 +0200",
            "finished_at": "Mon, 25 Aug 2025 15:56:44 +0200",
            "metadata": {
              "bsp-sha256": "a5603553e0eaad133719dc19b57c96e811a72af5329e120310f96b4fdc891732"
            }
          },
          {
            "run_id": "976c3d37-0b9a-4c81-ad0d-ebb96c9eee94",
            "config_name": "config2.yaml"
            "test_suite_name": "complex-test"
            "status": "running",
            "created_at": "Mon, 25 Aug 2025 16:58:35 +0200",
            "started_at": "Mon, 25 Aug 2025 16:58:36 +0200",
            "finished_at": "",
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
    :status 404: config file was not found

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

    :>json string id: test run identifier
    :>json string created_at: UTC creation time (RFC822)
    :>json string started_at: UTC creation time (RFC822)
    :>json string finished_at: UTC completion time (RFC822)
    :>json string status: test run status, one of:
        * pending   - accepted but not started
        * running   - currently executing
        * finished  - completed successfully
        * failed    - error during execution
        * aborted   - stopped by user or system
    :>json dict[str, str] metadata: optional test run metadata (key/value pairs)

    **Example Request**

    .. sourcecode:: http

        GET /api/v1/test-runs/25d9f4a2-2556-4647-b3cc-762348dc51ce HTTP/1.1

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "run_id": "25d9f4a2-2556-4647-b3cc-762348dc51ce",
          "config_name": "config1.yaml"
          "test_suite_name": "simple-test"
          "status": "finished",
          "created_at": "Mon, 25 Aug 2025 15:56:35 +0200",
          "started_at": "Mon, 25 Aug 2025 15:56:36 +0200",
          "finished_at": "Mon, 25 Aug 2025 15:56:44 +0200",
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

        DELETE /api/v1/test-runs/25d9f4a2-2556-4647-b3cc-762348dc51ce HTTP/1.1

    **Example Response**

    .. sourcecode:: http

        HTTP/1.1 200 OK
        Content-Type: application/json

        {
          "run_id": "25d9f4a2-2556-4647-b3cc-762348dc51ce",
          "config_name": "config1.yaml"
          "test_suite_name": "simple-test"
          "status": "aborted",
          "created_at": "Mon, 25 Aug 2025 15:56:35 +0200",
          "finished_at": "Mon, 25 Aug 2025 15:56:44 +0200",
          "metadata": {
            "bsp-sha256": "a5603553e0eaad133719dc19b57c96e811a72af5329e120310f96b4fdc891732"
          }
        }
    """  # noqa: E501
    #TODO: Add implementation
    return {}, 200


@test_runs_blueprint.route("/api/v1/test-runs/<int:identifier>/report")
def fetch_test_run_report(identifier: int):
    """Fetch test run report

    :param identifier: test run identifier
    :status 200: no error
    :status 404: test run not completed or does not exist, or report file does not exist

    :>file text/csv: CSV file containing the full test report

    **Example request**

        GET /api/v1/test-runs/25d9f4a2-2556-4647-b3cc-762348dc51ce/report HTTP/1.1

    **Example response**

        HTTP/1.1 200 OK
        Content-Type: text/csv
        Content-Disposition: attachment; filename="25d9f4a2-2556-4647-b3cc-762348dc51ce.csv"

        device name,test name,module,duration,message,status
        enp14s0,exist,test.py::TestNetwork::test_exist,0.0007359918672591448,,passed

    """  # noqa: E501
    #TODO: Add implementation
    return {}, 200
@test_runs_blueprint.route(
    "/api/v1/test-runs/<string:identifier>/artifacts/<path:artifact_name>")
def fetch_artifact(identifier: str, artifact_name: str):
    """Fetch test run artifact.

    :param identifier: test run identifier
    :param artifact_name: artifact filename
    :status 200: no error, file returned
    :status 404: test run not completed or does not exist, or artifact does not exist

    :>file: artifact file with content type inferred automatically

    **Example request**

        GET /api/v1/runs/25d9f4a2-2556-4647-b3cc-762348dc51ce/artifacst/frame.raw HTTP/1.1

    **Example response**

        HTTP/1.1 200 OK
        Content-Type: <depends on artifact>
        Content-Disposition: attachment; filename="frame.raw"
    """  # noqa: E501
    #TODO: Add implementation
    return {}, 200

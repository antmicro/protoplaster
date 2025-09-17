from flask import Blueprint, jsonify, request, current_app, send_from_directory
import os
from protoplaster.runner.metadata import RunStatus

test_runs_blueprint: Blueprint = Blueprint("protoplaster-test-runs", __name__)


@test_runs_blueprint.route("/api/v1/test-runs")
def fetch_test_runs():
    """Fetch a list of test runs

    :status 200: no error

    :>jsonarr string run_id: run id
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
    manager = current_app.config["RUN_MANAGER"]
    runs = manager.list_runs()
    return jsonify(runs)


@test_runs_blueprint.route("/api/v1/test-runs", methods=["POST"])
def trigger_test_run():
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
    data = request.get_json()
    config_name = data["config_name"]

    config_dir = current_app.config["ARGS"].test_dir
    config_path = os.path.join(config_dir, config_name)

    if not os.path.isfile(config_path):
        return jsonify({"error": "Configuration file not found"}), 404

    manager = current_app.config["RUN_MANAGER"]
    args = current_app.config["ARGS"]
    print("creating test run")
    run = manager.create_run(config_name, args)
    return jsonify(run), 200


@test_runs_blueprint.route("/api/v1/test-runs/<string:identifier>")
def fetch_one_test_run(identifier: str):
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
    manager = current_app.config["RUN_MANAGER"]
    run = manager.get_run(identifier)

    if run is None:
        return jsonify({"error": f"Run not found: {identifier}"}), 404

    return jsonify(run)


@test_runs_blueprint.route("/api/v1/test-runs/<string:identifier>",
                           methods=["DELETE"])
def delete_test_run(identifier: str):
    """Cancel a pending test run

    :param identifier: test run identifier
    :status 200: no error
    :status 400: test run not pending
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
    manager = current_app.config["RUN_MANAGER"]
    run = manager.cancel_run(identifier)
    if not run:
        return jsonify({"error": "Test run not found"}), 404

    if run.get("status") != RunStatus.PENDING:
        return jsonify({"error": "Test run not pending"}), 400

    run = manager.cancel_run(identifier)

    return jsonify(run)


@test_runs_blueprint.route("/api/v1/test-runs/<string:identifier>/report")
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
    manager = current_app.config["RUN_MANAGER"]
    run = manager.get_run(identifier)
    if not run:
        return jsonify({"error": "Test run not found"}), 404

    if (run.get("status") == RunStatus.PENDING
            or run.get("status") == RunStatus.RUNNING):
        return jsonify({"error": "Test run not finished"}), 404

    report_dir = current_app.config["ARGS"].reports_dir
    report_file = identifier + ".csv"
    report_path = os.path.join(report_dir, report_file)

    if not os.path.isfile(report_path):
        return jsonify({"error": "Report file not found"}), 404

    return send_from_directory(os.path.abspath(report_dir),
                               report_file,
                               as_attachment=True,
                               mimetype="text/csv")


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
    manager = current_app.config["RUN_MANAGER"]
    run = manager.get_run(identifier)
    if not run:
        return jsonify({"error": "Test run not found"}), 404

    if (run.get("status") == RunStatus.PENDING
            or run.get("status") == RunStatus.RUNNING):
        return jsonify({"error": "Test run not finished"}), 404

    artifacts_dir = current_app.config["ARGS"].artifacts_dir
    artifact_path = os.path.join(artifacts_dir, identifier, artifact_name)

    if not os.path.isfile(artifact_path):
        return jsonify({"error": "Artifact file not found"}), 404

    return send_from_directory(os.path.abspath(
        os.path.join(artifacts_dir, identifier)),
                               artifact_name,
                               as_attachment=True)

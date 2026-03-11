from flask import Blueprint, request, Response
import pickle
import importlib
from protoplaster.tools.log import error

execution_blueprint: Blueprint = Blueprint("protoplaster-execution", __name__)


@execution_blueprint.route("/api/v1/exec", methods=["POST"])
def execute_function():
    """Execute a function from a module

    :<json string module: module name to import
    :<json string function: function name to call
    :<json list args: (optional) arguments to pass to the function

    :status 200: function executed successfully
    :status 400: missing parameters
    :status 404: module or function not found
    :status 500: execution error

    :>json any result: return value of the function
    """
    data = pickle.loads(request.data)
    module_name = data.get("module")
    function_name = data.get("function")
    args = data.get("args", [])

    if not module_name or not function_name:
        return Response(pickle.dumps(
            {"error": "Module and function names are required"}),
                        status=400,
                        mimetype="application/octet-stream")

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return Response(pickle.dumps(
            {"error": f"Module {module_name} not found"}),
                        status=404,
                        mimetype="application/octet-stream")

    try:
        func = getattr(module, function_name)
    except AttributeError:
        return Response(pickle.dumps(
            {"error": f"Function {function_name} not found in {module_name}"}),
                        status=404,
                        mimetype="application/octet-stream")

    try:
        result = func(*args)
        return Response(pickle.dumps({"result": result}),
                        status=200,
                        mimetype="application/octet-stream")
    except Exception as e:
        print(
            error(
                f"RPC Execution failed while calling {func.__name__} with args: {args}: {e}"
            ))
        return Response(pickle.dumps({"error": str(e)}),
                        status=500,
                        mimetype="application/octet-stream")

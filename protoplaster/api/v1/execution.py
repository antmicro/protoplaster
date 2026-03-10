from flask import Blueprint, request
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
        return pickle.dumps(
            {"error": "Module and function names are required"}), 400

    try:
        module = importlib.import_module(module_name)
    except ImportError:
        return pickle.dumps({"error": f"Module {module_name} not found"}), 404

    try:
        func = getattr(module, function_name)
    except AttributeError:
        return pickle.dumps(
            {"error":
             f"Function {function_name} not found in {module_name}"}), 404

    try:
        result = func(*args)
        return pickle.dumps({"result": result})
    except Exception as e:
        print(
            error(
                f"RPC Execution failed while calling {func.__name__} with args: {args}: {e}"
            ))
        return pickle.dumps({"error": str(e)}), 500

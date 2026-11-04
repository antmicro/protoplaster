import traceback
from flask import Blueprint, request, Response
import pickle
import importlib
import protoplaster.tools.auth as auth
from protoplaster.conf.consts import SECURE_SIGNATURE_HEADER
from protoplaster.tools.log import error

execution_blueprint: Blueprint = Blueprint("protoplaster-execution", __name__)


def _response(payload: dict, status: int = 200) -> Response:
    body = pickle.dumps(payload)
    signature = auth.sign(body)

    return Response(
        body,
        status=status,
        mimetype="application/octet-stream",
        headers={SECURE_SIGNATURE_HEADER: signature},
    )


@execution_blueprint.route("/api/v1/exec", methods=["POST"])
def execute_function():
    """Execute a function from a module

    :<json string module: module name to import
    :<json string function: function name to call
    :<json list args: (optional) arguments to pass to the function

    :status 200: function executed successfully
    :status 400: missing parameters
    :status 401: missing or invalid signature
    :status 404: module or function not found
    :status 500: execution error

    :>json any result: return value of the function
    """

    if not auth.verify(request.headers.get(SECURE_SIGNATURE_HEADER),
                       request.data):
        return _response({"error": "Missing or invalid signature"}, 401)

    data = pickle.loads(request.data)
    module_name = data.get("module")
    function_name = data.get("function")
    args = data.get("args", [])

    if not module_name or not function_name:
        return _response({"error": "Module and function names are required"},
                         400)

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        return _response(
            {
                "error":
                f"While importing {module_name}: module {e.name} not found"
            }, 404)

    try:
        func = getattr(module, function_name)
    except AttributeError:
        return _response(
            {"error": f"Function {function_name} not found in {module_name}"},
            404)

    try:
        result = func(*args)
        return _response({"result": result})
    except Exception as e:
        print(
            error(
                f"RPC Execution failed while calling {func.__name__} with args: {args}: {e}"
            ))
        tb = "\n".join(traceback.format_exc().splitlines()[:-1])
        return _response({"error": str(e), "traceback": tb}, 500)

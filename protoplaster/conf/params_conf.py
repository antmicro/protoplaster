import pytest
import inspect
import yaml
import copy
from .plugin_manager import pm


def pytest_addoption(parser):
    parser.addoption("--yaml_file",
                     action="store",
                     type=str,
                     help="Test description yaml")
    parser.addoption("--artifacts-dir",
                     action="store",
                     type=str,
                     help="Directory where tests can store artifacts")
    parser.addoption(
        "--machine-target",
        action="store",
        type=str,
        default=None,
        help=
        "Target node name assigned when triggered remotely by the orchestrator. Internal parameter used by protoplaster; do not set manually."
    )


def _load_yaml_config(yaml_path):
    with open(yaml_path) as file:
        content = yaml.safe_load(file)
    res = {}
    execution_order = 0
    for group_key in content:
        for mod in content[group_key]:
            # convert {"key": {...}} to tuple ("key", {...})
            mod_name, mod_conf = next(iter(mod.items()))
            res.setdefault(mod_name, [])
            # store the intended execution order
            mod_conf["_execution_order"] = execution_order
            execution_order += 1
            res[mod_name].append(mod_conf)
    for mod in res:
        for i in range(len(res[mod])):
            if "__path__" in res[mod][i]:
                order = res[mod][i].get("_execution_order")
                res[mod][i] = res[mod][i]["tests"]
                res[mod][i]["_execution_order"] = order
    return res


def pytest_configure(config):
    """
    Pytest hook that runs exactly once per session.
    We load the YAML here and store it on the config object so all tests share it.
    """
    yaml_path = config.getoption("--yaml_file")
    if yaml_path:
        config._protoplaster_yaml_config = _load_yaml_config(yaml_path)


def pytest_generate_tests(metafunc):
    """
    Pytest hook called during the test collection phase.

    Pytest calls this hook once for every test function/method it collects,
    and generates multiple variations of the base function before execution.
    """
    if metafunc.cls is not None:
        yaml_config = getattr(metafunc.config, "_protoplaster_yaml_config",
                              None)
        if not yaml_config:
            raise AttributeError(
                f"{yaml_config=}, is _protoplaster_yaml_config set?")

        # Determine the module name for the current class
        try:
            module_name = metafunc.cls.module_name()
        except AttributeError:
            return

        if module_name in yaml_config:
            configs = yaml_config[module_name]
            metafunc.parametrize("test_config", configs, scope="class")


def save_class_state(cls):
    """Save the original state of the class."""
    original_state = {}
    for k, v in cls.__dict__.items():
        if k not in ('__dict__', '__weakref__'):
            try:
                original_state[k] = copy.deepcopy(v)
            except (TypeError, ValueError):
                # fallback if the object cannot be deepcopied (i.e: staticmethods)
                original_state[k] = v
    return original_state


def restore_class_state(cls, original_state):
    """Restore the class to its original state."""
    for key in list(cls.__dict__.keys()):
        if key not in original_state and key not in ('__dict__',
                                                     '__weakref__'):
            try:
                delattr(cls, key)
            except AttributeError:
                pass

    for key, value in original_state.items():
        try:
            setattr(cls, key, value)
        except AttributeError:
            pass


@pytest.fixture(autouse=True)
def run_before_and_after_tests(request):
    """Fixture to execute hooks before and after a test is run"""
    test_function = request._pyfuncitem.obj
    test_instance = test_function.__self__

    pm.hook.before_test_function(test_instance=test_instance,
                                 test_function=test_function)

    # execute test
    yield

    # guaranteed to run regardless of what happens in the tests.
    pm.hook.after_test_function(test_instance=test_instance,
                                test_function=test_function)


@pytest.fixture(scope='class', autouse=True)
def setup_tests(request: pytest.FixtureRequest, test_config):
    """
    Setup the test class with the specific configuration for this run.
    The 'test_config' argument is injected by pytest_generate_tests.

    This includes logic to clear the modified class/function state (self)
    during teardown. This is a workaround for the Pytest class singleton.
    """
    # save the original class state before modifying it
    original_state = save_class_state(request.cls)

    request.cls.machine_target = request.config.getoption("--machine-target")
    conf = test_config
    for key in conf:
        setattr(request.cls, key, conf[key])

    pm.hook.before_test_setup(test_class=request.cls)

    if hasattr(request.cls, "configure"):
        func = getattr(request.cls, "configure")

        if inspect.ismethod(func):
            func()
        else:
            func(request.cls)

    # execute tests
    yield

    if hasattr(request.cls, "deconfigure"):
        func = getattr(request.cls, "deconfigure")

        if inspect.ismethod(func):
            func()
        else:
            func(request.cls)

    # restore original state
    restore_class_state(request.cls, original_state)


def pytest_collection_modifyitems(items):
    """
    Pytest hook to sort the collected tests so they execute
    in the exact order specified in the YAML file.
    """

    def get_execution_order(item):
        if hasattr(item, "callspec") and "test_config" in item.callspec.params:
            conf = item.callspec.params["test_config"]
            return conf.get("_execution_order", float('inf'))
        return float('inf')

    items.sort(key=get_execution_order)


@pytest.fixture
def artifacts_dir(request):
    return request.config.getoption("--artifacts-dir")


@pytest.fixture
def record_artifact(request):
    artifacts = []

    request.node._artifacts = artifacts

    def _record(name: str):
        artifacts.append(name)

    yield _record

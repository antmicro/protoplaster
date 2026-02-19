import pytest
import inspect
import yaml
import copy


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
    for group_key in content:
        for mod in content[group_key]:
            # convert {"key": {...}} to tuple ("key", {...})
            mod_name, mod_conf = next(iter(mod.items()))
            res.setdefault(mod_name, [])
            res[mod_name].append(mod_conf)
    for mod in res:
        for i in range(len(res[mod])):
            if "__path__" in res[mod][i]:
                res[mod][i] = res[mod][i]["tests"]
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
            return

        # Determine the module name for the current class
        try:
            module_name = metafunc.cls.module_name()
        except AttributeError:
            return

        if module_name in yaml_config:
            configs = yaml_config[module_name]
            metafunc.parametrize("test_config", configs, scope="class")


@pytest.fixture(scope='class', autouse=True)
def setup_tests(request, test_config):
    """
    Setup the test class with the specific configuration for this run.
    The 'test_config' argument is injected by pytest_generate_tests.

    This includes logic to clear the modified class/function state (self)
    during teardown. This is a workaround for the Pytest class singleton.
    """
    # save the original class state before modifying it
    original_state = {}
    for k, v in request.cls.__dict__.items():
        if k not in ('__dict__', '__weakref__'):
            try:
                original_state[k] = copy.deepcopy(v)
            except TypeError:
                # fallback if the object cannot be deepcopied (i.e: staticmethods)
                original_state[k] = v

    request.cls.machine_target = request.config.getoption("--machine-target")
    conf = test_config
    for key in conf:
        setattr(request.cls, key, conf[key])

    if hasattr(request.cls, "configure"):
        func = getattr(request.cls, "configure")

        if inspect.ismethod(func):
            func()
        else:
            func(request.cls)

    # execute tests
    yield

    # restore original state
    for key in list(request.cls.__dict__.keys()):
        if key not in original_state and key not in ('__dict__',
                                                     '__weakref__'):
            try:
                delattr(request.cls, key)
            except AttributeError:
                pass

    for key, value in original_state.items():
        try:
            setattr(request.cls, key, value)
        except AttributeError:
            pass


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

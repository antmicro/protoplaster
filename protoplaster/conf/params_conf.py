import pytest
import yaml


def pytest_addoption(parser):
    parser.addoption("--yaml_file",
                     action="store",
                     type=str,
                     help="Test description yaml")
    parser.addoption("--artifacts-dir",
                     action="store",
                     type=str,
                     help="Directory where tests can store artifacts")


@pytest.fixture(scope='class', autouse=True)
def setup_tests(yaml_file, request):
    arg_name = request.cls.module_name()
    if arg_name in yaml_file:
        conf = yaml_file[arg_name].pop(0)
        for key in conf:
            setattr(request.cls, key, conf[key])


@pytest.fixture(scope='session')
def yaml_file(request):
    with open(request.config.getoption("--yaml_file")) as file:
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

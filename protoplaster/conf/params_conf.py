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
        thing = next(yaml_file[arg_name])
        for key in thing:
            setattr(request.cls, key, thing[key])


@pytest.fixture(scope='session')
def yaml_file(request):
    with open(request.config.getoption("--yaml_file")) as file:
        content = yaml.safe_load(file)
    content = {
        mod_key: content[group_key][mod_key]
        for group_key in content
        for mod_key in content[group_key]
    }
    for c in content:
        if '__path__' in content[c]:
            content[c] = content[c]['tests']
        if not isinstance(content[c], list):
            content[c] = [content[c]]
    content = {
        c: content[c] if isinstance(content[c], list) else [content[c]]
        for c in content
    }
    return {k: iter(content[k]) for k in content}


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

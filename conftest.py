import pytest
import yaml


def pytest_addoption(parser):
    parser.addoption(
        "--yaml_file", action="store", type=str, help="Test description yaml"
    )

@pytest.fixture(scope='class', autouse=True)
def callattr_ahead_of_alltests(yaml_file, request):
    arg_name = request.cls.module_name()
    if arg_name in yaml_file:
        thing = next(yaml_file[arg_name])
        for key in thing:
            setattr(request.cls, key, thing[key])


@pytest.fixture(scope='module')
def yaml_file(request):
    with open(request.config.getoption("--yaml_file")) as file:
        content = yaml.safe_load(file)
    return {k: iter(content[k]) for k in content}


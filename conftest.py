import pytest
import yaml


def pytest_addoption(parser):
    parser.addoption(
        "--yaml_file", action="store", type=str, help="Test description yaml"
    )

@pytest.fixture
def yaml_file(request):
    with open(request.config.getoption("--yaml_file")) as file:
        content = yaml.safe_load(file)
    return content


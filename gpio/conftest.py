import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--number", action="store", type=int, required=True, help="GPIO number"
    )
    parser.addoption(
        "--value", action="store", type=str, required=True, help="GPIO expected value"
    )

@pytest.fixture
def number(request):
    return request.config.getoption("--number")

@pytest.fixture
def value(request):
    return request.config.getoption("--value")


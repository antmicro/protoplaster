import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--bus", action="store", type=int, required=True, help="I2C bus to test"
    )
    parser.addoption(
        "--address", action="append", type=str, required=True, help="Address to check"
    )

@pytest.fixture
def bus(request):
    return request.config.getoption("--bus")

@pytest.fixture
def addresses(request):
    return [int(i, 16) for i in request.config.getoption("--address")]

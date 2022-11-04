import pytest
from camera import Camera


def pytest_addoption(parser):
    parser.addoption(
        "--device", action="store", type=str, default="/dev/video0", help="Device path"
    )
    parser.addoption(
        "--camera_name", action="store", type=str, required=True, help="Camera name"
    )
    parser.addoption(
        "--driver_name", action="store", type=str, required=True, help="Driver name"
    )

@pytest.fixture
def device(request):
    return Camera(request.config.getoption("--device"))

@pytest.fixture
def camera_name(request):
    return request.config.getoption("--camera_name")

@pytest.fixture
def driver_name(request):
    return request.config.getoption("--driver_name")

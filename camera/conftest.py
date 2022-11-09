import pytest
from camera.camera import Camera

@pytest.fixture
def camera(yaml_file):
    return yaml_file['camera'] if 'camera' in yaml_file else []

@pytest.fixture
def camera_device(yaml_file):
    return [Camera(i['device']) for i in yaml_file['camera']] if 'camera' in yaml_file else []

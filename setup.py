import os
from setuptools import find_packages, setup


def read_req(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()


setup(
    name="protoplaster",
    scripts=['protoplaster/protoplaster'],
    version="1.0",
    description=
    "An automated framework for platform testing (Hardware and BSPs)",
    author="Antmicro Ltd",
    license=
    'Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
    packages=find_packages(),
    include_package_data=True,
    package_data={'': ['template.md']},
    install_requires=read_req('requirements.txt').splitlines(),
)

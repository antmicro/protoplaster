from setuptools import find_packages, setup

setup(
    name="protoplaster",
    packages=find_packages(),
    scripts=['protoplaster/protoplaster'],
    version="1.0",
    description=
    "An automated framework for platform testing (Hardware and BSPs)",
    author="Antmicro Ltd",
    license=
    'Apache Software License (http://www.apache.org/licenses/LICENSE-2.0)',
    include_package_data=True,
    install_requires=[
        'pytest==5.3.5',
        'pyyaml==5.3.1',
        'smbus2==0.3.0',
        'colorama==0.3.9',
        'Jinja2==3.1.2',
        'MarkupSafe==2.1.1',
        'pyrav4l2 @ git+https://github.com/antmicro/pyrav4l2.git@7d4dc36a8f#egg=pyrav4l2',
    ])

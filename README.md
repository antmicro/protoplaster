# Protoplaster

Copyright (c) 2022-2025 [Antmicro](https://www.antmicro.com)

An automated framework for platform testing (Hardware and BSPs).

Currently includes tests for:

* I2C
* GPIO
* Camera
* FPGA

## Installation
```bash
pip install git+https://github.com/antmicro/protoplaster.git
```

## Usage

```
usage: protoplaster [-h] [-d TEST_DIR] [-r REPORTS_DIR] [-a ARTIFACTS_DIR]
                    [-t TEST_FILE] [-g GROUP] [-s TEST_SUITE] [--list-groups]
                    [--list-test-suites] [--list-tests] [-o OUTPUT]
                    [--csv CSV] [--csv-columns CSV_COLUMNS] [--generate-docs]
                    [-c CUSTOM_TESTS] [--report-output REPORT_OUTPUT]
                    [--system-report-config SYSTEM_REPORT_CONFIG] [--sudo]
                    [--server] [--port PORT]
                    [--external-devices EXTERNAL_DEVICES]

options:
  -h, --help            show this help message and exit
  -d, --test-dir TEST_DIR
                        Path to the test directory
  -r, --reports-dir REPORTS_DIR
                        Path to the reports directory
  -a, --artifacts-dir ARTIFACTS_DIR
                        Path to the test artifacts directory
  -t, --test-file TEST_FILE
                        Path to the yaml test description in the test
                        directory
  -g, --group GROUP     Group to execute [deprecated]
  -s, --test-suite TEST_SUITE
                        Test suite to execute
  --list-groups         List possible groups to execute [deprecated]
  --list-test-suites    List possible test suites to execute
  --list-tests          List all defined tests
  -o, --output OUTPUT   A junit-xml style report of the tests results
  --csv CSV             Generate a CSV report of the tests results
  --csv-columns CSV_COLUMNS
                        Comma-separated list of columns to be included in
                        generated CSV
  --generate-docs       Generate documentation
  -c, --custom-tests CUSTOM_TESTS
                        Path to the custom tests sources
  -l, --log             Append test results to a log file
  --report-output REPORT_OUTPUT
                        Proplaster report archive
  --system-report-config SYSTEM_REPORT_CONFIG
                        Path to the system report yaml config file
  --sudo                Run as sudo
  --server              Run in server mode
  --port PORT           Port to use when running in server mode
  --external-devices EXTERNAL_DEVICES
                        Path to yaml config file with additional external
                        devices
```

Protoplaster expects a yaml file describing tests as an input. The yaml file should have a structure specified as follows:

<!-- name="example" -->
```yaml
includes:
  - addition.yml        # Import additional definitions from external file

tests:
  base:                 # Test name
  - i2c:                # A module specifier
      bus: 0            # An interface specifier
      devices:          # Multiple instances of devices can be defined in one module
      - name: "Sensor name"
        address: 0x3c   # The given device parameters determine which tests will be run for the module
      - name: "I2C-bus multiplexer"
        address: 0x70
  - camera:
      device: "/dev/video0"
      camera_name: "vivid"
      driver_name: "vivid"
  - camera:
      device: "/dev/video2"
      camera_name: "vivid"
      driver_name: "vivid"
      save_file: "frame.raw"
  additional:
  - gpio:
      number: 20
      value: 1

metadata:               # Additional metadata to be generated on tested device
  uname:                # Metadata name
    run: uname -r       # Command to run

test-suites:
  basic:                # Test suite name
    tests:              # Tests to include
      - base
  full:
    tests:
      - basic           # Test suites can include other test suites
      - additional
    metadata:           # Metadata to generate for this test
      - uname
```

### Test suites
In the YAML file, you can define different groups of tests in the `test-suites` section
to run them for different use cases.
In the YAML file example, there are two suites defined: `basic` and `full`.
Protoplaster, when run without a defined test suite, will execute all tests defined in given file.
When the test suite is specified with the parameter `-s` or `--test-suite`,
only the tests in the specified suite are going to be run.
You can also list existing groups in the YAML file, simply run `protoplaster --list-test-suites test.yaml`.

### External Devices

When running in server mode, you can provide a YAML configuration file to automatically register external devices using the `--external-devices` argument.

The configuration file should be a YAML dictionary mapping device names to their IP addresses or URLs:

```yaml
node1: 10.0.1.2
node2: 10.0.1.3:2100
lab_device: http://192.168.1.50:8037
```

## Base modules parameters
Each base module requires parameters for test initialization. 
These parameters describe the tests and are passed to the test class as its attributes.

### I2C
Required parameters:

* `bus` - i2c bus to be checked
* `name` - name of device to be detected
* `address` - address of the device to be detected on the indicated bus

### GPIO
Required parameters:

* `number` - GPIO pin number
* `value` - value written to, or expected to be read from that pin

Optional parameters:

* `gpio_name` - name of the sysfs GPIO interface after exporting
* `write` - whether to configure the pin as an output and assert that the written value is preserved, otherwise perform a read and assert that the read value matches the specified value (default: false)

### Cameras
Required parameters:

* `device` - path to the camera device (eg. /dev/video0)
* `camera_name` - expected camera name
* `driver_name` - expected driver name

Optional parameters:

* `save_file` - a path which the tested frame is saved to (the frame is saved only if this parameter is present)

### FPGA
Required parameters:

* `sysfs_interface` - path to a sysfs interface for flashing the bitstream to the FPGA
* `bitstream_path` - path to a test bitstream that is going to be flashed

## Writing additional modules
Apart from the base modules available in Protoplaster, you can provide your own additional modules.

Each custom module should follow this structure:
```
{module_name}/
|- __init__.py
|- test.py
|- <optional helper files>
```
Here, `module_name` must match the name of the test module. For example, in the sample below, it would be `additional_camera`.

By default, external modules are expected in the `--TEST_DIR` directory. If you want to store them elsewhere, you can use the `--custom-tests` argument to specify a custom path.

The `test.py` file must define a test class decorated with `ModuleName(test_module)` from the `protoplaster.conf.module` package. This decorator specifies the name of the module, allowing Protoplaster to correctly initialize the test parameters.

The test class must also implement a `name()` method, whose return value is used for the `device_name` field in the CSV output.

All individual tests should be implemented within the main class in `test.py`. The class name must start with `Test`, and every test method within it must start with `test`.

An example of an extended module test:

```python
from protoplaster.conf.module import ModuleName


@ModuleName("additional_camera")
class TestAdditionalCamera:
    """
    {% macro TestAdditionalCamera(prefix) -%}
    Additional camera tests
    -----------------------
    {% do prefix.append('') %}
    This module provides tests dedicated to camera sensors on specific video node:
    {%- endmacro %}
    """

    def test_exists(self):
        """
        {% macro test_exists(device) -%}
          check if the path exists
        {%- endmacro %}
        """
        assert self.path == "/dev/video0"
```

And a YAML definition:

```yaml
---
base:
  additional_camera:
    - path: "/dev/video0"
    - path: "/dev/video1"
```

## Protoplaster test report
Protoplaster provides `protoplaster-test-report`, a tool to convert test CSV output into a HTML or Markdown table.
```
usage: protoplaster-test-report [-h] [-i INPUT_FILE] -t {md,html} [-o OUTPUT_FILE]

options:
  -h, --help            show this help message and exit
  -i INPUT_FILE, --input-file INPUT_FILE
                        Path to the csv file
  -t {md,html}, --type {md,html}
                        Output type
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Path to the output file
```


## System report
Protoplaster provides `protoplaster-system-report`, a tool for obtaining information about system state and configuration.
It executes a list of commands and saves their outputs. 
The outputs are stored in a single zip archive along with an HTML summary.

### Usage
```
usage: protoplaster-system-report [-h] [-o OUTPUT_FILE] [-c CONFIG] [--sudo]

options:
  -h, --help            show this help message and exit
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        Path to the output file
  -c CONFIG, --config CONFIG
                        Path to the YAML config file
  --sudo                Run as sudo
```

The YAML config contains a list of actions to perform. A single action is described as follows:

```yaml
report_item_name:
  run: script
  summary:
    - title: summary_title
      run: summary_script
  output: script_output_file
  superuser: required | preferred
  on-fail: ...
```

* `run` - command to be run
* `summary` – a list of summary generators, each one with fields:
  * `title` – summary title
  * `run` – command that generates the summary. This command gets the output of the original command as stdin. This field is optional; if not specified, the output is placed in the report as-is.
* `output` - output file for the output of `run`.
* `superuser` – optional, should be specified if the command requires elevated privileges to run. Possible values:
  * `required` – `protoplaster-system-report` will terminate if the privilege requirement is not met
  * `preferred` – if the privilege requirement is not met, a warning will be issued and this particular item won't be included in the report
* `on-fail` – optional description of an item to run in case of failure. It can be used to run an alternative command when the original one fails or is not available.

Example config file:
<!-- name="system-report-example" -->
```yaml
uname:
  run: uname -a
  summary:
    - title: os info
      run: cat
  output: uname.out
dmesg:
  run: dmesg
  summary: 
    - title: usb
      run: grep usb
    - title: v4l
      run: grep v4l
  output: dmesg.out
  superuser: required
ip:
  run: ip a
  summary:
    - title: Network interfaces state
      run: python3 $PROTOPLASTER_SCRIPTS/generate_ip_table.py "$(cat)"
  output: ip.out
  on-fail:
    run: ifconfig -a
    summary:
      - title: Network interfaces state
        run: python3 $PROTOPLASTER_SCRIPTS/generate_ifconfig_table.py "$(cat)"
    output: ifconfig.out
```

### Running as root
By default, `sudo` doesn't preserve `PATH`. 
To run `protoplaster-system-report` installed by a non-root user as root, invoke `protoplaster-system-report --sudo`

## Protoplaster manager
Protoplaster provides `protoplaster-mgmt`, a tool to remotely control Protoplaster via the API.
For more detailed information, see the help messages associated with each subcommand.

```
usage: protoplaster-mgmt [-h] [--url URL] [--config CONFIG] [--config-dir CONFIG_DIR] [--report-dir REPORT_DIR] [--artifact-dir ARTIFACT_DIR] {configs,runs} ...

Tool for managing Protoplaster via remote API

options:
  -h, --help            show this help message and exit
  --url URL             URL to a device running Protoplaster server (default: http://127.0.0.1:5000/)
  --config CONFIG       Config file with values for url, config-dir, report-dir, artifact-dir
  --config-dir CONFIG_DIR
                        Directory to save fetched config (default: ./)
  --report-dir REPORT_DIR
                        Directory to save a test report (default: ./)
  --artifact-dir ARTIFACT_DIR
                        Directory to save a test artifact (default: ./)

available commands:
  {configs,runs}
    configs             Configs management
    runs                Test runs management

```

# Plaster

Copyright (c) 2022 [Antmicro](https://www.antmicro.com)

An automated framework for platform testing (Hardware and BSPs).

Currently includes tests for:

* I2C
* GPIO
* Camera

## Usage

To use, clone the repository and install the requirements:

```bash
git clone https://github.com/antmicro/plaster.git
cd plaster/
pip install requirements.txt
```

And then execute the tests for the selected subsystems.

### I2C
`pytest i2c/test.py --bus=1 --address="0x3c"`

### GPIO
`pytest gpio/test.py --number=22 --value=1`

### Cameras
`pytest camera/test.py --device="/dev/video0" --camera_name="Camera name" --driver_name="camera-driver"`

There is a possibility to save a frame to a file, in that case pass the file name to `--save_file=""`

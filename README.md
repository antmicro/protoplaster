# Plaster

An automated framework for testing hardware. It includes tests for:

* I2C
* GPIO
* Camera

## Installation
To use the framework you first need to clone the repository, and install requirements:

```bash
git clone https://github.com/antmicro/plaster.git
cd plaster/
pip install requirements.txt
```

## Usage
### I2C
`pytest i2c/test.py --bus=1 --address="0x3c"`

### GPIO
`pytest gpio/test.py --number=22 --value=1`

### Cameras
`pytest camera/test.py --device="/dev/video0" --camera_name="Camera name" --driver_name="camera-driver"`

There is a possibility to save the frame to a file, in that case pass the file name to `--save_file=""`

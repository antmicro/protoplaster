class I2C:
    def __init__(self, address):
        self.address = address

    def check_connection(self):
        pass

    @staticmethod
    def i2cdetect():
        pass    # This one is static

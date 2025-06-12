import socket


class NETWORK:

    def __init__(self, interface):
        self.interface = interface

    def check_existence(self):
        interfaces = [i[1] for i in socket.if_nameindex()]

        return self.interface in interfaces

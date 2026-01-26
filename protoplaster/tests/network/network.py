import socket
import os


class NETWORK:

    def __init__(self, interface):
        self.interface = interface

    def check_existence(self):
        interfaces = [i[1] for i in socket.if_nameindex()]

        return self.interface in interfaces

    def read_speed(self):
        speed_path = f"/sys/class/net/{self.interface}/speed"
        if os.path.exists(speed_path):
            try:
                with open(speed_path, "r") as f:
                    return int(f.read().strip())
            except (OSError, ValueError):
                pass
        return None

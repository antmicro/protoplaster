class CustomPickleObject:
    """
    A custom class to test that pickle can reconstruct arbitrary
    objects across the RPC calls.
    """

    def __init__(self, byte_data: bytes, set_data: set):
        self.byte_data = byte_data
        self.set_data = set_data

    def __repr__(self):
        return f"CustomPickleObject(bytes={self.byte_data}, set={self.set_data})"


def remote_pickle_echo(byte_arg: bytes, set_arg: set) -> CustomPickleObject:
    """
    Executes on the remote device.
    Verifies the types of incoming arguments and returns a custom class instance.
    """
    print(f"remote_pickle_echo received: bytes={byte_arg}, set={set_arg}")

    assert isinstance(byte_arg, bytes), f"Expected bytes, got {type(byte_arg)}"
    assert isinstance(set_arg, set), f"Expected set, got {type(set_arg)}"
    return CustomPickleObject(byte_data=byte_arg, set_data=set_arg)

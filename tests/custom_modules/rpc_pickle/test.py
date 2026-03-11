from protoplaster.tools.tools import trigger_on_remote
from protoplaster.conf.module import ModuleName
from rpc_pickle.utils import remote_pickle_echo, CustomPickleObject


@ModuleName("rpc_pickle")
class TestPickleRPC:

    def configure(self):
        assert hasattr(self, "dev"), "dev parameter required in yaml"

    def test_custom_objects_rpc(self):
        """
        Test sending and receiving non-JSON serializable objects over RPC.
        Sends: bytes, set
        Receives: CustomPickleObject instance
        """
        test_bytes = b"\x00\xFF\xAAtest_bytes"
        test_set = {"apple", "banana", 42}

        print(f"[{self.dev}] Sending bytes and set to remote via RPC...")

        result = trigger_on_remote(self.dev, remote_pickle_echo,
                                   [test_bytes, test_set])

        print(f"[{self.dev}] Received result: {result}")
        print(f"[{self.dev}] Result type: {type(result)}")

        assert isinstance(result, CustomPickleObject), \
            f"Expected CustomPickleObject, got {type(result)}"

        assert result.byte_data == test_bytes, \
            f"Byte data mismatch: expected {test_bytes}, got {result.byte_data}"

        assert result.set_data == test_set, \
            f"Set data mismatch: expected {test_set}, got {result.set_data}"

        print(
            "SUCCESS: Pickle RPC serialization verified for bytes, sets, and custom classes!"
        )

    def name(self):
        return f"Pickle RPC Serialization Test ({self.dev})"

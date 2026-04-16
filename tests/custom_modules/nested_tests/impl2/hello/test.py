from protoplaster.conf.module import ModuleName

@ModuleName("nested_tests/impl2/hello")
class TestHello2:

    def configure(self):
        pass

    def test_hello2(self):
        assert self.message == "World", f"Expected `World` message attribute, got: {self.message}"

    def name(self):
        return f"Hello Test (impl2): {self.message}"

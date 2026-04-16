from protoplaster.conf.module import ModuleName

@ModuleName("nested_tests/impl1/hello")
class TestHello:

    def configure(self):
        pass

    def test_hello(self):
        assert self.message == "Hello", f"Expected `Hello` message attribute, got: {self.message}"

    def name(self):
        return f"Hello Test (impl1): {self.message}"

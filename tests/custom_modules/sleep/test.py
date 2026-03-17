from protoplaster.conf.module import ModuleName
import time

@ModuleName("sleep")
class TestSleepRPC:

    def configure(self):
        pass

    def test_sleep(self):
        time.sleep(10)

    def name(self):
        return f"Sleep Test"

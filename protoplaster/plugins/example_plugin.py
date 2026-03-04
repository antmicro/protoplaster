from typing import Callable

from protoplaster.conf.plugin_manager import hookimpl


class ProtoplasterPlugin:

    @hookimpl
    def before_test_function(self, test_instance, test_function: Callable):
        print(f"hello from {test_instance.name()}", test_instance,
              test_function.__name__)

    @hookimpl
    def after_test_function(self, test_instance, test_function: Callable):
        print(f"goodbye from {test_instance.name()}", test_instance,
              test_function.__name__)

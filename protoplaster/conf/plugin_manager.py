from pathlib import Path
from pluggy import HookimplMarker, HookspecMarker, PluginManager
import importlib

from protoplaster.conf.consts import PROTOPLASTER
from protoplaster.tools.tools import pr_warn, pr_info

hookspec = HookspecMarker(PROTOPLASTER)
hookimpl = HookimplMarker(PROTOPLASTER)


class ProtoplasterSpec:

    @hookspec
    def before_test_function(self, test_instance, test_function):
        """called before test function, but after the configure method"""

    @hookspec
    def after_test_function(self, test_instance, test_function):
        """called after test function"""


pm = PluginManager(PROTOPLASTER)
pm.add_hookspecs(ProtoplasterSpec)


def load_plugins_from_dir(folder: str):
    folder_path = Path(folder)
    if not folder_path.is_dir():
        pr_warn(f"Not a directory: {folder}")
        return

    for file_path in folder_path.iterdir():
        if file_path.is_file(
        ) and file_path.suffix == ".py" and not file_path.name.startswith(
                "__"):
            modulename = file_path.stem
            spec = importlib.util.spec_from_file_location(
                modulename, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if hasattr(module, "ProtoplasterPlugin"):
                plugin_class = getattr(module, "ProtoplasterPlugin")
                pm.register(plugin_class())
                pr_info(f"Registered plugin: {plugin_class}")

import inspect
import functools


class BaseTest:
    machines = None


class ModuleName(object):

    def __init__(self, name):
        self.module_name = name

    def __call__(self, test_class):
        # Build the members dict manually using reversed MRO and __dict__.
        # We avoid inspect.getmembers() because it sorts alphabetically,
        # and we want to preserve the exact order the tests were defined in the file.
        # First, all test_metods of the derived class are executed, and then the methods of the base class
        members = {}
        for base_class in test_class.__mro__:
            for name in base_class.__dict__:
                members.setdefault(name, getattr(test_class, name))

        for name, member in members.items():
            if (name.startswith("test") and
                (inspect.ismethod(member) or inspect.isfunction(member))):
                # setting attribute does not change order in __dict __ if it is already set
                # to achive correct order we first have to delete it, and then set it again
                try:
                    delattr(test_class, name)
                except AttributeError:
                    pass
                setattr(test_class, name, member)

        name_method = getattr(test_class, "name", None)
        if not callable(name_method):
            raise TypeError("Class is missing name() method")

        @staticmethod
        def module_name():
            return self.module_name

        setattr(test_class, "module_name", module_name)
        return test_class

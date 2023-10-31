import inspect


def ReportDeviceName(f):

    def wrapper(self, record_property):
        record_property("device", self.name())
        return f(self)

    return wrapper


class ModuleName(object):

    def __init__(self, name):
        self.module_name = name

    def __call__(self, *param_arg):
        for name, member in inspect.getmembers(param_arg[0]):
            if (name.startswith("test") and
                (inspect.ismethod(member) or inspect.isfunction(member))):
                setattr(param_arg[0], name, ReportDeviceName(member))

        name_method = getattr(param_arg[0], "name", None)
        if not callable(name_method):
            raise TypeError("Class is missing name() method")

        @staticmethod
        def module_name():
            return self.module_name

        setattr(param_arg[0], "module_name", module_name)
        return param_arg[0]

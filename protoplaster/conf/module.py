import inspect
import functools


def report_device_name(f):
    # pytest passes fixtures to tests if given test contains parameter with that name,
    # we want tu use record_property fixture in wrapper, but out wrapped function may
    # not have it on its param list, so we have handle such case

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if 'record_property' in inspect.signature(f).parameters.keys():
            record_property = kwargs['record_property']
        else:
            # wrapped function doesn't expect record_property arg, we have to remove it
            record_property = kwargs.pop('record_property')
        record_property("device", args[0].name())
        return f(*args, **kwargs)

    if 'record_property' not in inspect.signature(f).parameters.keys():
        # extend wrapper function signature with record_property param
        wrapped_sig = inspect.signature(f)
        new_params = list(wrapped_sig.parameters.values()) + [
            inspect.Parameter('record_property',
                              inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        wrapper.__signature__ = wrapped_sig.replace(parameters=new_params)
    return wrapper


class BaseTest:
    machines = None


class ModuleName(object):

    def __init__(self, name):
        self.module_name = name

    def __call__(self, *param_arg):
        for name, member in inspect.getmembers(param_arg[0]):
            if (name.startswith("test") and
                (inspect.ismethod(member) or inspect.isfunction(member))):
                setattr(param_arg[0], name, report_device_name(member))

        name_method = getattr(param_arg[0], "name", None)
        if not callable(name_method):
            raise TypeError("Class is missing name() method")

        @staticmethod
        def module_name():
            return self.module_name

        setattr(param_arg[0], "module_name", module_name)
        return param_arg[0]

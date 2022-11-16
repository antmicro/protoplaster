class ModuleName(object):

    def __init__(self, name):
        self.module_name = name

    def __call__(self, *param_arg):

        @staticmethod
        def module_name():
            return self.module_name

        setattr(param_arg[0], "module_name", module_name)
        return param_arg[0]

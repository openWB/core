import inspect


def get_default(cls, param):
    sig = inspect.signature(cls.__init__)
    return sig.parameters[param].default

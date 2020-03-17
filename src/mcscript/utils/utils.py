import warnings
from functools import wraps


class Map(dict):
    """
    Dictionary that can be accessed using the dot
    """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delattr__


def deprecated(reason="deprecated"):
    def _deprecated(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(f"for {func}: {reason}", DeprecationWarning, 2)
            return func(*args, **kwargs)

        # noinspection PyDeprecation
        return wrapper

    return _deprecated

import warnings
from functools import wraps


def deprecated(reason="deprecated"):
    def _deprecated(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(f"for {func}: {reason}", DeprecationWarning, 2)
            return func(*args, **kwargs)

        # noinspection PyDeprecation
        return wrapper

    return _deprecated


def run_function_once(func):
    """ On Classes will run once for the class, not for each object.  """
    hasRun = False

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal hasRun
        if not hasRun:
            hasRun = True
            return func(*args, **kwargs)
        return None

    return wrapper

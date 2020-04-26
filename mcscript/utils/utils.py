import warnings
from functools import wraps

from mcscript import Logger


def requiresMcVersion(version: int, message=""):
    """
    Functions annotated with this decorator will fail if the current selected version below `version`.

    Args:
        version: the version as integer
        message: A message to show when the version is too low

    Raises:
        RuntimeError
    """
    from mcscript.utils.cmdHelper import getCurrentWorld

    def decorator(func):
        _checked = False

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal _checked
            if not _checked:
                if getCurrentWorld() is not None:
                    if not getCurrentWorld().satisfiesVersion(version):
                        raise RuntimeError(
                            f"Function {func} does not support version {getCurrentWorld().mcVersion['Id'].value}. "
                            f"Minimum version: {version}:\n{message}"
                        )
                else:
                    warnings.warn(f"Cannot verify minimum required version {version} for {func}")
                _checked = True

            return func(*args, **kwargs)

        return wrapper

    return decorator


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
    cache = None

    @wraps(func)
    def wrapper(*args, **kwargs):
        nonlocal hasRun, cache
        if not hasRun:
            hasRun = True
            cache = func(*args, **kwargs)
        return cache

    return wrapper


def debug_log_text(text: str, message):
    """Debug logs a multi-line text and annotates it with line numbers."""
    text = text.strip().split("\n")
    padding = len(str(len(text)))
    debug_code = "\n\t".join(f"[{str(index + 1).zfill(padding)}] {i}" for index, i in enumerate(text))
    Logger.debug(f"{message}\n\t{debug_code}")

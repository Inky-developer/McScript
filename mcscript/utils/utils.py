from __future__ import annotations

import warnings
from functools import wraps
from typing import TYPE_CHECKING

from mcscript import Logger

if TYPE_CHECKING:
    from mcscript.data.Config import Config


def requiresMcVersion(version: int, message=""):
    """
    Functions annotated with this decorator will fail if the current selected version below `version`.

    Args:
        version: the version as integer
        message: A message to show when the version is too low

    Raises:
        RuntimeError
    """
    from mcscript.data.Config import Config

    def decorator(func):
        _checked = False

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal _checked
            if not _checked:
                if Config.currentConfig.world is not None:
                    if not Config.currentConfig.world.satisfiesVersion(version):
                        raise RuntimeError(
                            f"Function {func} does not support version "
                            f"{Config.currentConfig.world.mcVersion['Id'].value}. "
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

        # LOL
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


def string_format(config: Config, string: str, **kwargs: str) -> str:
    kwargs.setdefault("name", config.project_name)
    kwargs.setdefault("name2", config.project_name)
    return string.format(**kwargs)


def camel_case_to_snake_case(string: str) -> str:
    """ 
    Converts a CamelCase word to a snake_case word.
    >>> camel_case_to_snake_case("HelloWorld")
    'hello_world'
    >>> camel_case_to_snake_case("ThisIsA_LongText")
    'this_is_a_long_text'
    """
    characters = []
    previous = None
    for index, character in enumerate(string):
        if character.isupper() and index != 0 and previous != "_":
            characters.append("_")
        characters.append(character.lower())
        previous = characters[-1]

    return "".join(characters)

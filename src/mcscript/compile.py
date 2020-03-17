from typing import Callable, Any

from . import Grammar, PreCompiler, Compiler
from .data.Config import Config
from .data.defaultCode import addDefaults
from .utils.Datapack import Datapack

eventCallback = Callable[[str, float, Any], Any]


def compileMcScript(text: str, callback: eventCallback, config: Config) -> Datapack:
    """
    compiles a McScript and returns the generated datapack.
    :param text: the script
    :param callback: a callback which gets called when a component is starting
    :param config: the configuration for this build
    :return:
    """
    steps = (
        (lambda string: Grammar.parse(string), "Parsing"),
        (lambda ast: PreCompiler().compile(ast), "Evaluating static elements"),
        (lambda arg: Compiler.compile(*arg, text, config), "Compiling"),
        (lambda datapack: addDefaults(datapack), "post processing")
    )

    arg = text
    for index, step in enumerate(steps):
        callback(step[1], index / len(steps), arg)
        arg = step[0](arg)

    callback("Done", 1, arg)
    return arg

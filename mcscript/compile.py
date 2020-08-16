from logging import DEBUG
from time import perf_counter
from typing import Callable

import lark
from lark import Tree

from mcscript import get_compiler, get_grammar, Logger
from mcscript.analyzer.Analyzer import Analyzer
from mcscript.backends import get_default_backend
from mcscript.backends.mc_datapack_backend.Datapack import Datapack
from mcscript.data.Config import Config
from mcscript.exceptions.exceptions import McScriptError
from mcscript.exceptions.parseExceptions import McScriptParseException
from mcscript.utils.utils import debug_log_text

NUM_COMPILE_STEPS = 4


def compileMcScript(config: Config, callback: Callable = None) -> Datapack:
    """
    compiles a mcscript string and returns the generated datapack.

    Args:
        callback: a callback function that accepts the current state, the progress and the temporary object
        config: the config. Should contain the input file and the target path

    Returns:
        A datapack
    """
    steps = (
        (_parseCode, "Parsing"),
        (lambda tree: Analyzer().analyze(tree), "Analyzing context"),
        (lambda tree: get_compiler().compile(tree[0], tree[1], text, config), "Compiling"),
        (lambda ir_master: get_default_backend()(config, ir_master).generate(), "Running ir backend")
    )

    text = config.input_file

    if Logger.isEnabledFor(DEBUG):
        debug_log_text(text, "[Compile] parsing the following code: ")

    global_start_time = perf_counter()

    arg = text
    for index, step in enumerate(steps):
        if callback is not None:
            callback(step[1], index / len(steps), arg)
        start_time = perf_counter()
        try:
            arg = step[0](arg)
        except Exception as e:
            if not isinstance(e, McScriptError):
                Logger.critical(f"Internal compiler error occurred: {repr(e)}")
            raise e
        Logger.info(f"{step[1]} finished in {perf_counter() - start_time:.4f} seconds")
        if isinstance(arg, Tree):
            _debug_log_tree(arg)

    if callback is not None:
        callback("Done", 1, arg)

    Logger.info(f"Run all steps in {perf_counter() - global_start_time:.4f} seconds")

    # noinspection PyTypeChecker
    return arg


def _parseCode(code: str) -> Tree:
    try:
        # keeping tabs can produce error messages that are offset
        return get_grammar().parse(code.replace("\t", "  "))
    except lark.exceptions.UnexpectedToken as e:
        # noinspection PyUnresolvedReferences
        raise McScriptParseException(e.line, e.column, code, e.expected, e.token) from None


def _debug_log_tree(tree: Tree):
    if Logger.isEnabledFor(DEBUG):
        debug_log_text(tree.pretty(), "[Compile] Intermediate Tree:")

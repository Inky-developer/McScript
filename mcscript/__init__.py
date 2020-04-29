import logging
from importlib import resources
from os.path import join

from lark import Lark

from mcscript.utils.dirPaths import getLogDir

# setting up the logger as early as possible
Logger = logging.getLogger("McScript")
Logger.setLevel(logging.DEBUG)

# clear logging file
fPath = join(getLogDir(), "latest.log")
open(fPath, "w+").close()
_fh = logging.FileHandler(fPath, encoding="utf-8")
_fh.setLevel(logging.DEBUG)

_ch = logging.StreamHandler()
_ch.setLevel(logging.INFO)

_formatter = logging.Formatter("[%(levelname)s] [%(name)s] %(message)s")
_fh.setFormatter(_formatter)
_ch.setFormatter(_formatter)

Logger.addHandler(_ch)
Logger.addHandler(_fh)

Logger.info("Logger initialized")

from mcscript.compiler.Compiler import Compiler as _Compiler

Grammar = Lark(
    resources.read_text("mcscript", "McScript.lark"),
    parser="lalr",
    propagate_positions=True,
    maybe_placeholders=True
)

Compiler = _Compiler()

Logger.info("Grammar loaded")

__all__ = "Grammar", "Compiler", "Logger"

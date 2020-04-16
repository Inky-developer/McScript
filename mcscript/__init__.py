import logging
from importlib import resources

from lark import Lark

# setting up the logger as early as possible

Logger = logging.getLogger("McScript")
Logger.setLevel(logging.DEBUG)

# clear logging file
open("../latest.log", "w+").close()
_fh = logging.FileHandler("../latest.log", encoding="utf-8")
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
    resources.open_text("mcscript", "McScript.lark").read(),
    parser="lalr",
    propagate_positions=True,
    maybe_placeholders=True
)

Compiler = _Compiler()

Logger.info("Grammar loaded")

__all__ = "Grammar", "Compiler", "Logger"

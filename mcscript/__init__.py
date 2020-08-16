from __future__ import annotations

import logging
from importlib import resources
from os.path import join
from typing import TYPE_CHECKING

from lark import Lark

from mcscript.utils.dirPaths import LOG_DIRECTORY

if TYPE_CHECKING:
    from mcscript.compiler.Compiler import Compiler

__version__ = "0.0.1"

# setting up the logger as early as possible
Logger = logging.getLogger("McScript")
Logger.setLevel(logging.DEBUG)

# clear logging file
fPath = join(LOG_DIRECTORY, "latest.log")
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
Logger.info(f"Logfile at {fPath}")

GLOBAL_GRAMMAR = None
JSON_MARKUP_GRAMMAR = None
SELECTOR_GRAMMAR = None
GLOBAL_COMPILER = None


def get_grammar() -> Lark:
    global GLOBAL_GRAMMAR
    if GLOBAL_GRAMMAR is None:
        GLOBAL_GRAMMAR = Lark(
            resources.read_text("mcscript", "McScript.lark"),
            parser="lalr",
            propagate_positions=True,
            maybe_placeholders=True
        )
        Logger.debug("Grammar loaded")
    return GLOBAL_GRAMMAR


def get_json_markup_grammar() -> Lark:
    global JSON_MARKUP_GRAMMAR
    if JSON_MARKUP_GRAMMAR is None:
        JSON_MARKUP_GRAMMAR = Lark(
            resources.read_text("mcscript", "textMarkup.lark"),
            parser="lalr",
            maybe_placeholders=True,
            # cache=True
        )
        Logger.debug("[JsonTextFormat] Loaded grammar textMarkup")
    return JSON_MARKUP_GRAMMAR


def get_selector_grammar() -> Lark:
    global SELECTOR_GRAMMAR
    if SELECTOR_GRAMMAR is None:
        SELECTOR_GRAMMAR = Lark(
            resources.read_text("mcscript", "selector.lark"),
            # The nbt matcher does not work with lalr
            parser="earley",
            maybe_placeholders=False,
            propagate_positions=True,
        )
        Logger.debug("[Selector] Grammar loaded!")
    return SELECTOR_GRAMMAR


def get_compiler() -> Compiler:
    global GLOBAL_COMPILER
    if GLOBAL_COMPILER is None:
        from mcscript.compiler.Compiler import Compiler
        GLOBAL_COMPILER = Compiler()
    return GLOBAL_COMPILER


__all__ = ("get_grammar", "get_json_markup_grammar", "get_selector_grammar", "get_compiler", "Logger")

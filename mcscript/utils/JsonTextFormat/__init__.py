from importlib import resources

from lark import Lark

from mcscript import Logger

markupGrammar = Lark(
    resources.read_text("mcscript", "textMarkup.lark"),
    parser="lalr",
    maybe_placeholders=True
)
Logger.info("[JsonTextFormat] Loaded grammar textMarkup")

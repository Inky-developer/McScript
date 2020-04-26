from importlib import resources

from lark import Lark

markupGrammar = Lark(
    resources.read_text("mcscript", "textMarkup.lark"),
    parser="lalr",
    maybe_placeholders=True
)
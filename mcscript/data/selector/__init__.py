from importlib import resources

from lark import Lark

from mcscript import Logger

selectorGrammar = Lark(
    resources.read_text("mcscript", "selector.lark"),
    # The nbt matcher does not work with lalr
    parser="earley",
    maybe_placeholders=False,
    propagate_positions=True
)
Logger.info("[Selector] Grammar loaded!")

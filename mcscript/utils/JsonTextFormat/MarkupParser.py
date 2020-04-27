from __future__ import annotations

import json
from typing import Dict, TYPE_CHECKING

from lark import UnexpectedToken
from lark.visitors import Interpreter

from mcscript import Logger
from mcscript.Exceptions.compileExceptions import McScriptArgumentsError, McScriptError, McScriptInvalidMarkupError
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.utils.JsonTextFormat import markupGrammar
from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
from mcscript.utils.JsonTextFormat.objectFormatter import format_bold, format_color, format_hover, format_italic, \
    format_obfuscated, \
    format_open_url, format_run_command, format_strike_through, format_text, format_underlined
from mcscript.utils.utils import debug_log_text

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState

RULE2ACTION = {
    "b"      : lambda v, c: format_bold(c),
    "i"      : lambda v, c: format_italic(c),
    "u"      : lambda v, c: format_underlined(c),
    "s"      : lambda v, c: format_strike_through(c),
    "o"      : lambda v, c: format_obfuscated(c),
    "color"  : lambda v, c: format_color(c, str(v)),
    "link"   : lambda v, c: format_open_url(c, v),
    "command": lambda v, c: format_run_command(c, v),
    "hover"  : lambda v, c: format_hover(c, v)
}


class MarkupParser(Interpreter):
    def __init__(self, compileState: CompileState):
        self.state: Dict = {}
        self.compileState = compileState

    def toJsonString(self, markup: str, *args: Resource) -> str:
        result = self.toJson(markup, *args)
        if isinstance(result, list):
            result.insert(0, "")

        # Why is escaping so annoying?
        return json.dumps(result).replace("\\\\", "\\")

    def toJson(self, markup: str, *args: Resource) -> Dict:
        """
        Converts a markup string to a minecraft json format string.

        Args:
            markup: the markup string
            *args: resources to insert into the placeholders

        Returns:
            A json string
        """
        self.state = dict(args=args)
        try:
            Logger.debug(f"[MarkupParser] parsing '{markup}'")
            tree = markupGrammar.parse(markup)
            debug_log_text(tree.pretty(), "Parse tree: ")
            return self.visit(tree)
        except UnexpectedToken as e:
            raise McScriptInvalidMarkupError(f"\nFailed to parse Markup string:\n"
                                             f"{e.get_context(markup, span=len(markup))}"
                                             f"Unexpected token: {e.token.type}('{e.token}')\n"
                                             f"Expected one of {e.expected}", self.compileState)

    def string(self, tree):
        string, = tree.children
        return format_text(str(string).replace("\\[", "[").replace("\\]", "]"))

    def placeholder(self, tree):
        number, = tree.children
        if number is None:
            number = self.state.get("auto_index", 0)
            self.state["auto_index"] = number + 1
        else:
            number = int(number)

        try:
            resource = self.state["args"][number]
            return ResourceTextFormatter(self.compileState).createFromResource(resource)
        except IndexError:
            raise McScriptArgumentsError(
                f"Invalid number of arguments, requires at least {number + 1} "
                f"but got {len(self.state['args'])}", self.compileState
            ) from None

    def markup_rule(self, tree):
        rule, value, *content, endRule = tree.children

        if rule != endRule:
            raise McScriptInvalidMarkupError(f"Rule mismatch: {rule} was ended with {endRule}", self.compileState)

        ret = []
        for i in content:
            data = self.visit(i)
            ret.append(data)

        # if ret contains only one element, we can directly format on that
        if len(ret) == 1:
            content = ret[0]
        else:
            content = {
                "text" : "",
                "extra": ret
            }

        try:
            return RULE2ACTION[rule](value, content)
        except Exception as e:
            raise McScriptError(e, self.compileState)

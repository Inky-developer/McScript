from __future__ import annotations

import json
from typing import TYPE_CHECKING, List

from mcscript.data.selector.Selector import Selector
from mcscript.exceptions.exceptions import McScriptUnexpectedTypeError
from mcscript.ir.components import MessageNode, StoreFastVarFromResultNode, CommandNode, StoreFastVarNode
from mcscript.lang.atomic_types import String, Any, Null, Int
from mcscript.lang.resource.IntegerResource import IntegerResource
from mcscript.lang.resource.MacroResource import MacroResource
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.functionSignature import FunctionParameter
from mcscript.lang.std import macro
from mcscript.utils.JsonTextFormat.MarkupParser import MarkupParser
from mcscript.utils.JsonTextFormat.objectFormatter import format_text, format_score
from mcscript.utils.Scoreboard import Scoreboard
from mcscript.utils.resources import ScoreboardValue

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


def create_text_functions() -> List[MacroResource]:
    """
    Creates all text output functions and returns them

    Returns:
        A list of all text functions
    """

    def make_function(f_name: str, f_msg_type: MessageNode.MessageType):
        @macro(
            parameters=[
                FunctionParameter("text", String, accepts=FunctionParameter.ResourceMode.STATIC),
                FunctionParameter("parameters", Any, FunctionParameter.ParameterCount.ARBITRARY)
            ],
            return_type=Null,
            name=f_name
        )
        def function(compile_state: CompileState, string: StringResource, *parameters: Resource):
            compile_state.ir.append(MessageNode(
                f_msg_type,
                MarkupParser(compile_state).to_json_string(string.static_value, *parameters)
            ))

        return function

    ret = []
    for name, msg_type in (
            ("print", MessageNode.MessageType.CHAT),
            ("actionbar", MessageNode.MessageType.ACTIONBAR),
            ("title", MessageNode.MessageType.TITLE),
            ("subtitle", MessageNode.MessageType.SUBTITLE)
    ):
        ret.append(make_function(name, msg_type))
    return ret


@macro(
    parameters=[
        FunctionParameter("resource", Any, accepts=FunctionParameter.ResourceMode.STATIC)
    ],
    return_type=Any
)
def dyn(compile_state: CompileState, resource: Resource) -> Resource:
    """ Stores a static resource onto a scoreboard"""
    r = resource.store(compile_state)
    if isinstance(r, ValueResource):
        r.static_value = None
    return r


@macro(
    parameters=[
        FunctionParameter("scoreboard", String),
        FunctionParameter("score", String),
        FunctionParameter("resource", Any),
    ],
    return_type=Null
)
def set_score(compile_state: CompileState, scoreboard: StringResource, score: StringResource,
              resource: Resource) -> Resource:
    """ Extremely temporary test function"""
    if not isinstance(resource, ValueResource):
        raise McScriptUnexpectedTypeError("set_score", resource.type(), "<Supports scoreboard>", compile_state)

    scoreboard = Scoreboard(scoreboard.static_value, True, len(compile_state.ir.scoreboards))
    compile_state.ir.scoreboards.append(scoreboard)

    resource = resource.store(compile_state)
    scoreboard_value = ScoreboardValue(score.static_value, scoreboard)
    compile_state.ir.append(StoreFastVarNode(
        scoreboard_value,
        resource.scoreboard_value
    ))

    # to prevent the node from getting optimized out
    compile_state.ir.append(MessageNode(
        MessageNode.MessageType.CHAT,
        json.dumps([format_text("The test result is: "), format_score(scoreboard_value)]),
        Selector("a", [])
    ))
    return NullResource()


@macro(
    parameters=[
        FunctionParameter("string", String, accepts=FunctionParameter.ResourceMode.STATIC)
    ],
    return_type=Int,
)
def evaluate(compile_state: CompileState, string: StringResource) -> IntegerResource:
    """ Evaluates the string at runtime and returns the result"""
    stack = compile_state.expressionStack.next()
    compile_state.ir.append(StoreFastVarFromResultNode(
        stack,
        CommandNode(string.static_value)
    ))
    return IntegerResource(None, stack)


@macro(
    parameters=[
        FunctionParameter("string", String, accepts=FunctionParameter.ResourceMode.STATIC)
    ],
    return_type=Null,
)
def execute(compile_state: CompileState, string: StringResource) -> NullResource:
    """ Executes the string at runtime and returns Null"""
    compile_state.ir.append(CommandNode(string.static_value))
    return NullResource()


# Pycharm cannot apply the type macro at type-check time (Which actually creates a MacroResource)
# noinspection PyTypeChecker
EXPORTS: List[MacroResource] = [
    *create_text_functions(),
    dyn,
    set_score,
    evaluate,
    execute,
]

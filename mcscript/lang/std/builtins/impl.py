from __future__ import annotations

from typing import TYPE_CHECKING, List

from mcscript.ir.components import MessageNode
from mcscript.lang.resource.MacroResource import MacroResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.functionSignature import FunctionParameter
from mcscript.lang.std import macro
from mcscript.utils.JsonTextFormat.MarkupParser import MarkupParser

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
                FunctionParameter("text", ResourceType.STRING, accepts=FunctionParameter.ResourceMode.STATIC),
                FunctionParameter("parameters", ResourceType.ANY, FunctionParameter.ParameterCount.ARBITRARY)
            ],
            return_type=ResourceType.NULL,
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


EXPORTS = [] + create_text_functions()

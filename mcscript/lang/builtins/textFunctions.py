from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.ir.components import MessageNode
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.JsonTextFormat.MarkupParser import MarkupParser

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class TextFunction(BuiltinFunction, ABC):
    @abstractmethod
    def get_message_type(self) -> MessageNode.MessageType:
        pass

    def returnType(self) -> ResourceType:
        return ResourceType.NULL

    def requireRawParameters(self) -> bool:
        return True

    @staticmethod
    def inline():
        return True

    def generate(self, compileState: CompileState, *parameters: Resource) -> Resource:
        fmt_string, *resources = parameters
        compileState.ir.append(MessageNode(
            self.get_message_type(),
            MarkupParser(compileState).to_json_string(fmt_string.static_value, *resources)
        ))
        return NullResource()


class PrintFunction(TextFunction):
    """
    parameter => [Static] text: String the format string
    parameter => *values: Resource the values to print out
    Print Function.
    Example:
        aValue = 10
        print("Hello world! ", "The result is: ", aValue)
    """

    def get_message_type(self) -> MessageNode.MessageType:
        return MessageNode.MessageType.CHAT

    def name(self) -> str:
        return "print"


class TitleFunction(TextFunction):
    """
    parameter => [Static] text: String the format string
    parameter => *values: Resource the values to print out
    prints text as title
    """

    def get_message_type(self) -> MessageNode.MessageType:
        return MessageNode.MessageType.TITLE

    def name(self) -> str:
        return "title"


class SubTitleFunction(TextFunction):
    """
    parameter => [Static] text: String the format string
    parameter => *values: Resource the values to print out
    prints text as subtitle
    """

    def get_message_type(self) -> MessageNode.MessageType:
        return MessageNode.MessageType.SUBTITLE

    def name(self) -> str:
        return "subtitle"


class ActionBarFunction(TextFunction):
    """
    parameter => [Static] text: String the format string
    parameter => *values: Resource the values to print out
    prints text on the actionbar
    """

    def get_message_type(self) -> MessageNode.MessageType:
        return MessageNode.MessageType.ACTIONBAR

    def name(self) -> str:
        return "actionbar"

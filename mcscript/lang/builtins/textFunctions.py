from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.JsonTextFormat.MarkupParser import MarkupParser


class TextFunction(BuiltinFunction, ABC):
    @abstractmethod
    def getCommand(self) -> PrintCommand:
        pass

    def returnType(self) -> ResourceType:
        return ResourceType.NULL

    def requireRawParameters(self) -> bool:
        return True

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        fmtString: StringResource

        fmtString, *resources = parameters
        return FunctionResult(
            self.getCommand().value(text=MarkupParser(compileState).toJsonString(fmtString.value, *resources)),
            resource=NullResource(),
            inline=True
        )


if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class PrintFunction(TextFunction):
    """
    parameter => [Static] text: String the format string
    parameter => *values: Resource the values to print out
    Print Function.
    Example:
        aValue = 10
        print("Hello world! ", "The result is: ", aValue)
    """

    def getCommand(self) -> PrintCommand:
        return PrintCommand.TELLRAW

    def name(self) -> str:
        return "print"


class TitleFunction(TextFunction):
    """
    parameter => [Static] text: String the format string
    parameter => *values: Resource the values to print out
    prints text as title
    """

    def getCommand(self) -> PrintCommand:
        return PrintCommand.TITLE

    def name(self) -> str:
        return "title"


class SubTitleFunction(TextFunction):
    """
    parameter => [Static] text: String the format string
    parameter => *values: Resource the values to print out
    prints text as subtitle
    """

    def getCommand(self) -> PrintCommand:
        return PrintCommand.SUBTITLE

    def name(self) -> str:
        return "subtitle"


class ActionBarFunction(TextFunction):
    """
    parameter => [Static] text: String the format string
    parameter => *values: Resource the values to print out
    prints text on the actionbar
    """

    def getCommand(self) -> PrintCommand:
        return PrintCommand.ACTIONBAR

    def name(self) -> str:
        return "actionbar"

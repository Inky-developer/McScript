from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from mcscript.lang.ResourceTextFormatter import PrintCommand, ResourceTextFormatter
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class TextFunction(BuiltinFunction, ABC):
    @abstractmethod
    def getCommand(self) -> PrintCommand:
        pass

    def returnType(self) -> ResourceType:
        return ResourceType.NULL

    def requireRawParameters(self) -> bool:
        return True

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        return FunctionResult(
            ResourceTextFormatter(compileState).createCommandFromResources(self.getCommand(), *parameters),
            resource=NullResource(),
            inline=True
        )


class PrintFunction(TextFunction):
    """
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
    parameter => *values: Resource the values to print out
    prints text as title
    """

    def getCommand(self) -> PrintCommand:
        return PrintCommand.TITLE

    def name(self) -> str:
        return "title"


class SubTitleFunction(TextFunction):
    """
        parameter => *values: Resource the values to print out
        prints text as subtitle
        """

    def getCommand(self) -> PrintCommand:
        return PrintCommand.SUBTITLE

    def name(self) -> str:
        return "subtitle"


class ActionBarFunction(TextFunction):
    """
        parameter => *values: Resource the values to print out
        prints text on the actionbar
        """

    def getCommand(self) -> PrintCommand:
        return PrintCommand.ACTIONBAR

    def name(self) -> str:
        return "actionbar"

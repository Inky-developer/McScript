from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import Command
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.builtins.builtins import BuiltinFunction

if TYPE_CHECKING:
    from src.mcscript import CompileState


class EvaluateFunction(BuiltinFunction):
    """
    parameter => string: String the string to evaluate
    runs a minecraft function directly and returns the result
    """

    def name(self) -> str:
        return "evaluate"

    def returnType(self) -> ResourceType:
        return ResourceType.NUMBER

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        if len(parameters) != 1:
            raise McScriptArgumentsError(f"Function evaluate expected exactly one argument but got {len(parameters)}.")
        string = parameters[0]
        if string.type() != ResourceType.STRING or not string.hasStaticValue:
            raise McScriptArgumentsError(f"Function evaluate expected a string but got {repr(string)}")

        return Command.SET_VALUE_FROM(
            stack=compileState.config.RETURN_SCORE,
            command=string
        )

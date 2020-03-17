from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.builtins.builtins import BuiltinFunction
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class ExecuteFunction(BuiltinFunction):
    """
    runs a minecraft function directly and returns null
    """

    def name(self) -> str:
        return "execute"

    def returnType(self) -> ResourceType:
        return ResourceType.NULL

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        if len(parameters) != 1:
            raise McScriptArgumentsError(f"Function execute expected exactly one argument but got {len(parameters)}.")
        string = parameters[0]
        if string.type() != ResourceType.STRING or not string.hasStaticValue:
            raise McScriptArgumentsError(f"Function execute expected a string but got {repr(string)}")

        return string.embed()

from __future__ import annotations

from typing import Union, TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult

if TYPE_CHECKING:
    from src.mcscript import CompileState


class BooleanFunction(BuiltinFunction):
    """
    parameter => value
    """

    def name(self) -> str:
        return "boolean"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        if len(parameters) != 1:
            raise McScriptArgumentsError("Function boolean accepts exactly one argument")

        parameter = parameters[0].convertToBoolean(compileState)

        return FunctionResult(None, parameter)

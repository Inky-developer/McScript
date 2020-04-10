from __future__ import annotations

from typing import Union, TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptArgumentsError
from mcscript.lang.builtins.builtins import FunctionResult, BuiltinFunction
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


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

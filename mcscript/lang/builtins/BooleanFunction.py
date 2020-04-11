from __future__ import annotations

from typing import TYPE_CHECKING, Union

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class BooleanFunction(BuiltinFunction):
    """
    parameter => value: Resource the value that will be converted to a boolean
    """

    def name(self) -> str:
        return "boolean"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        parameter = parameters[0].convertToBoolean(compileState)

        return FunctionResult(None, parameter)

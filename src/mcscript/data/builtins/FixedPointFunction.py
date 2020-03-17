from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError, McScriptTypeError
from src.mcscript.data.builtins.builtins import FunctionResult, BuiltinFunction
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class FixedPointFunction(BuiltinFunction):
    """
    Converts a number to a fixed-point number.
    Current behavior: a number (eg. 10) will be the value of the fixed number,
    which means that the fixed number has a value of 10/1024.
    This Behavior will change in the future (toDo)
    Accepts exactly one parameter
    """

    def name(self) -> str:
        return "fixed"

    def returnType(self) -> ResourceType:
        return ResourceType.FIXED_POINT

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        if len(parameters) != 1:
            raise McScriptArgumentsError("Function fixed accepts exactly one argument")
        parameter, = parameters
        if isinstance(parameter, ValueResource):
            if parameter.hasStaticValue:
                try:
                    value = parameter.toNumber()
                except TypeError:
                    raise McScriptTypeError(
                        f"Parameter {parameter} could not be converted to a number for function fixed")
                return FunctionResult(None, resource=FixedNumberResource(value, True))
            else:
                stack = parameter.loadToScoreboard(compileState)
                return FunctionResult(None, resource=FixedNumberResource(stack, False))

        # if the parameter is not a value resource, try to convert it to a fixed point number
        try:
            resource = parameter.convertToFixedNumber(compileState)
        except TypeError:
            raise McScriptTypeError(f"Parameter {parameter} for function fixed cannot be converted.")
        return FunctionResult(None, resource)

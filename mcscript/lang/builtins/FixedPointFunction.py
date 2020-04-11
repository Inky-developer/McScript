from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptTypeError
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class FixedPointFunction(BuiltinFunction):
    """
    parameter => value: Number
    Converts a number to a fixed-point number.
    Current behavior: a number (eg. 10) will be the value of the fixed number,
    which means that the fixed number has a value of 10/1024.
    This Behavior will change in the future (toDo)
    """

    def name(self) -> str:
        return "fixed"

    def returnType(self) -> ResourceType:
        return ResourceType.FIXED_POINT

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        parameter, = parameters
        if isinstance(parameter, ValueResource):
            if parameter.hasStaticValue:
                try:
                    value = parameter.toNumber()
                except TypeError:
                    raise McScriptTypeError(
                        f"Parameter {parameter} could not be converted to a number for function fixed", compileState)
                return FunctionResult(None, resource=FixedNumberResource(value, True))
            else:
                stack = parameter.load(compileState)
                return FunctionResult(None, resource=FixedNumberResource(stack, False))

        raise NotImplementedError()

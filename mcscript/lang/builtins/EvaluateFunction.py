from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptArgumentsError
from mcscript.data.commands import Command
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class EvaluateFunction(BuiltinFunction):
    """
    parameter => string: String the string to evaluate
    runs a minecraft function directly and returns the result
    """

    def name(self) -> str:
        return "evaluate"

    def returnType(self) -> ResourceType:
        return ResourceType.NUMBER

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        if len(parameters) != 1:
            raise McScriptArgumentsError(f"Function evaluate expected exactly one argument but got {len(parameters)}.")
        string = parameters[0]
        if string.type() != ResourceType.STRING or not string.hasStaticValue:
            raise McScriptArgumentsError(f"Function evaluate expected a string but got {repr(string)}")

        stack = compileState.expressionStack.next()
        return FunctionResult(
            Command.SET_VALUE_FROM(
                stack=stack,
                command=string
            ), NumberResource(stack, False))

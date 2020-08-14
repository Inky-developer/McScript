from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.resource.base.ResourceType import ResourceType

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.IntegerResource import IntegerResource
from mcscript.lang.resource.base.ResourceBase import Resource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class EvaluateFunction(BuiltinFunction):
    """
    parameter => [Static] string: String the string to evaluate
    runs a minecraft function directly and returns the result
    """

    def name(self) -> str:
        return "evaluate"

    def returnType(self) -> ResourceType:
        return ResourceType.INTEGER

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        string, = parameters

        stack = compileState.expressionStack.next()
        return FunctionResult(
            Command.SET_VALUE_FROM(
                stack=stack,
                command=string
            ), IntegerResource(stack, False))

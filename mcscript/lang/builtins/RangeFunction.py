from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.TupleResource import TupleResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class RangeFunction(BuiltinFunction):
    """
    parameter => [Static] start: Number the start value. End value if the only parameter
    parameter => [Static] [Optional=Null] end: Number the end value
    parameter => [Static] [Optional=1] step: Number the step value

    creates an array using the start, end and step parameters. Behaves like the python `range` function
    """

    def name(self) -> str:
        return "range"

    def returnType(self) -> ResourceType:
        return ResourceType.TUPLE

    # noinspection PyTypeChecker
    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        start, end, step = parameters

        if isinstance(end, NullResource):
            start, end = 0, start

        start, end, step = int(start), int(end), int(step)

        if step == 0:
            raise self.ArgumentsError(parameters, f"Step must not be zero", compileState)
        if step > 0 and end < start:
            raise self.ArgumentsError(parameters, f"end must be greater than start for positive step", compileState)
        if step < 0 and start < end:
            raise self.ArgumentsError(parameters, f"end must be less than start for negative step", compileState)

        return FunctionResult(None, TupleResource(*[NumberResource(i, True) for i in range(start, end, step)]))

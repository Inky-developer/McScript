from __future__ import annotations

from typing import TYPE_CHECKING, Union

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.TupleResource import TupleResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class ArrayFunction(BuiltinFunction):
    """
    parameter => [Static] size: Number how big this array should be

    Creates an array with the specified size.
    This array is empty, which means it contains only NullResources
    Elements can be accessed via the [<index>] operator
    """

    def name(self) -> str:
        return "array"

    def returnType(self) -> ResourceType:
        return ResourceType.TUPLE

    def requireRawParameters(self) -> bool:
        """ If possible, use static resources"""
        return True

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        size, = parameters
        return FunctionResult(None, TupleResource(*[NullResource() for _ in range(size.toNumber())]))

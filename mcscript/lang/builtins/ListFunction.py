from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.ListResource import ListResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class ListFunction(BuiltinFunction):
    """
    parameter => [Static] type: Type the type that elements of the list must have

    Creates a List of the generic type `type`.
    """

    def name(self) -> str:
        return "list"

    def returnType(self) -> ResourceType:
        return ResourceType.LIST

    # noinspection PyTypeChecker
    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        resourceType, = parameters

        return FunctionResult(
            None,
            ListResource(resourceType)
        )

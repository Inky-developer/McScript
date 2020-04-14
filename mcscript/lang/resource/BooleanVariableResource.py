from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.VariableResource import VariableResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class BooleanVariableResource(VariableResource):
    """
    Used when a number is stored as a variable
    """

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.BOOLEAN

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self.load(compileState)

    def load(self, compileState: CompileState, stack: AddressResource = None) -> BooleanResource:
        stack = self._load(compileState, stack)
        return BooleanResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        target = self._copy(compileState, target)
        return BooleanVariableResource(target, False)

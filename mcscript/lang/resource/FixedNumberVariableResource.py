from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.VariableResource import VariableResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class FixedNumberVariableResource(VariableResource):
    """
    Used when a fixed number is stored as a variable on a nbt storage
    """

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.FIXED_POINT

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self.load(compileState).convertToBoolean(compileState)

    def load(self, compileState: CompileState, stack: ValueResource = None) -> FixedNumberResource:
        stack = self._load(compileState, stack)
        return FixedNumberResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        target = self._copy(compileState, target)
        return FixedNumberVariableResource(target, False)

    def operation_increment_one(self, compileState: CompileState) -> FixedNumberVariableResource:
        # 1. load self
        # 2. increment scoreboard value
        # 3. store back
        number = self.load(compileState)
        number = number.operation_plus(FixedNumberResource.fromNumber(1), compileState)
        return number.storeToNbt(self.value, compileState)

    def operation_decrement_one(self, compileState: CompileState) -> FixedNumberVariableResource:
        # 1. load self
        # 2. increment scoreboard value
        # 3. store back
        number = self.load(compileState)
        number = number.operation_minus(FixedNumberResource.fromNumber(1), compileState)
        return number.storeToNbt(self.value, compileState)

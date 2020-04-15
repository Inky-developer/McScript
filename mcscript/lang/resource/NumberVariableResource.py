from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import BinaryOperator
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.VariableResource import VariableResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class NumberVariableResource(VariableResource):
    """
    Used when a number is stored as a variable
    """

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NUMBER

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self.load(compileState).convertToBoolean(compileState)

    def load(self, compileState: CompileState, stack: ValueResource = None) -> NumberResource:
        stack = self._load(compileState, stack)
        return NumberResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        stack = self._copy(compileState, target)
        if not isinstance(stack, NbtAddressResource):
            return stack
        return NumberVariableResource(target, False)

    def operation_increment_one(self, compileState: CompileState) -> NumberVariableResource:
        # 1. load self
        # 2. increment scoreboard value
        # 3. store back
        number = self.load(compileState)
        number = number.numericOperation(NumberResource(1, True), BinaryOperator.PLUS, compileState)
        return number.storeToNbt(self.value, compileState)

    def operation_decrement_one(self, compileState: CompileState) -> NumberVariableResource:
        # 1. load self
        # 2. increment scoreboard value
        # 3. store back
        number = self.load(compileState)
        number = number.numericOperation(NumberResource(1, True), BinaryOperator.MINUS, compileState)
        return number.storeToNbt(self.value, compileState)

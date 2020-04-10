from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import Command, BinaryOperator
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import ValueResource, Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class NumberVariableResource(ValueResource):
    """
    Used when a number is stored as a variable
    """
    _hasStaticValue = False
    isDefault = False

    def embed(self) -> str:
        return str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, AddressResource) and not self.isStatic

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NUMBER

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self.load(compileState).convertToBoolean(compileState)

    def load(self, compileState: CompileState, stack: ValueResource = None) -> NumberResource:
        stack = stack or compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_VARIABLE(
            stack=stack,
            var=self.embed()
        ))
        return NumberResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        if not isinstance(target, NbtAddressResource):
            if isinstance(target, AddressResource):
                return self.load(compileState, target)
            raise ValueError(f"NumberVariableAddressResource expected NbtAddressResource, got {repr(target)}")
        compileState.writeline(Command.COPY_VARIABLE(
            address=target,
            address2=self.value
        ))
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

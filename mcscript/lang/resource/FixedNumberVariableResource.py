from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import Command
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class FixedNumberVariableResource(ValueResource):
    """
    Used when a fixed number is stored as a variable on a nbt storage
    """
    isDefault = False

    def embed(self) -> str:
        return str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, AddressResource) and not self.isStatic

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.FIXED_POINT

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self.load(compileState).convertToBoolean(compileState)

    def load(self, compileState: CompileState, stack: ValueResource = None) -> FixedNumberResource:
        stack = stack or compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_VARIABLE(
            stack=stack,
            scale=FixedNumberResource.BASE,
            var=self.embed()
        ))
        return FixedNumberResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState):
        if not isinstance(target, NbtAddressResource):
            if isinstance(target, AddressResource):
                return self.load(compileState, target)
            raise ValueError(f"FixedNumberVariableAddressResource expected NbtAddressResource, got {repr(target)}")
        compileState.writeline(Command.COPY_VARIABLE(
            address=target,
            address2=self.value
        ))
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
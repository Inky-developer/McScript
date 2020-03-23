from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.data.Commands import Command
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.NbtAddressResource import NbtAddressResource
from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


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

    def load(self, compileState: CompileState, stack: ValueResource = None) -> FixedNumberResource:
        stack = stack or compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_VARIABLE(
            stack=stack,
            var=self.embed()
        ))
        return FixedNumberResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState):
        if not isinstance(target, NbtAddressResource):
            raise RuntimeError(f"FixedNumberVariableAddressResource expected NbtAddressResource, got {repr(target)}")
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

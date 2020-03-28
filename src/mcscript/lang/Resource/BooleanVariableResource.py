from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.data.Commands import Command
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.BooleanResource import BooleanResource
from src.mcscript.lang.Resource.NbtAddressResource import NbtAddressResource
from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript.compiler.CompileState import CompileState


class BooleanVariableResource(ValueResource):
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
        return ResourceType.BOOLEAN

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self.load(compileState)

    def load(self, compileState: CompileState, stack: ValueResource = None) -> BooleanResource:
        stack = stack or compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_VARIABLE(
            stack=stack,
            var=self.embed()
        ))
        return BooleanResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState):
        if not isinstance(target, NbtAddressResource):
            raise RuntimeError(f"BooleanVariableAddressResource expected NbtAddressResource, got {repr(target)}")
        compileState.writeline(Command.COPY_VARIABLE(
            address=target,
            address2=self.value
        ))
        return BooleanVariableResource(target, False)

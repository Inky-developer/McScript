from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import Command
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


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
        compileState.writeline(Command.LOAD_SCORE(
            stack=stack,
            var=self.embed()
        ))
        return BooleanResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState):
        if not isinstance(target, NbtAddressResource):
            if isinstance(target, AddressResource):
                return self.load(compileState, target)
            raise ValueError(f"BooleanVariableAddressResource expected NbtAddressResource, got {repr(target)}")
        compileState.writeline(Command.COPY_VARIABLE(
            address=target,
            address2=self.value
        ))
        return BooleanVariableResource(target, False)

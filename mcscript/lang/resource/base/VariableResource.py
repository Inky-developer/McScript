from __future__ import annotations

from abc import ABC
from typing import Optional, TYPE_CHECKING

from mcscript.data.commands import Command
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import MinecraftDataStorage, Resource, ValueResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class VariableResource(ValueResource, ABC):
    """
    Represents a valueResource on data storage.
    """
    _hasStaticValue = False
    isDefault = False
    storage = MinecraftDataStorage.STORAGE

    def embed(self) -> str:
        return str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, NbtAddressResource) and self.isStatic

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> Resource:
        return self.copy(stack, compileState)

    def _load(self, compileState: CompileState, stack: Optional[AddressResource], scale=1) -> AddressResource:
        stack = stack or compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_SCORE(
            stack=stack,
            var=self.embed(),
            scale=scale
        ))
        return stack

    def _copy(self, compileState: CompileState, target: ValueResource) -> ValueResource:
        if not isinstance(target, NbtAddressResource):
            if isinstance(target, AddressResource):
                return self.load(compileState, target)
            raise ValueError(f"{type(self).__name__} expected NbtAddressResource, got {repr(target)}")
        compileState.writeline(Command.COPY_VARIABLE(
            address=target,
            address2=self.value
        ))
        return target

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from mcscript.data.commands import Command, ConditionalExecute, Relation
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import MinecraftDataStorage, Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.lang.resource.BooleanResource import BooleanResource
    from mcscript.lang.resource.NumberResource import NumberResource
    from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
    from mcscript.compiler.CompileState import CompileState


class VariableResource(ValueResource, ABC):
    """
    Represents a valueResource on data storage.
    """
    _hasStaticValue = False
    isDefault = False
    isVariable = True
    storage = MinecraftDataStorage.STORAGE

    @staticmethod
    @abstractmethod
    def type() -> ResourceType:
        pass

    def embed(self) -> str:
        return str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, NbtAddressResource) and self.isStatic

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> Resource:
        return self.copy(stack, compileState)

    def operation_test_relation(self, compileState: CompileState, relation: Relation,
                                other: Resource) -> ConditionalExecute:
        return self.load(compileState).operation_test_relation(compileState, relation, other)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self.load(compileState).convertToBoolean(compileState)

    def convertToNumber(self, compileState: CompileState) -> NumberResource:
        return self.load(compileState).convertToNumber(compileState)

    def convertToFixedNumber(self, compileState: CompileState) -> FixedNumberResource:
        return self.load(compileState).convertToFixedNumber(compileState)

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

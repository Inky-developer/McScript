from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from mcscript.ir.components import StoreFastVarNode
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import MinecraftDataStorage, Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.resources import ScoreboardValue

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

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self.load(compileState).convertToBoolean(compileState)

    def convertToNumber(self, compileState: CompileState) -> NumberResource:
        return self.load(compileState).convertToNumber(compileState)

    def convertToFixedNumber(self, compileState: CompileState) -> FixedNumberResource:
        return self.load(compileState).convertToFixedNumber(compileState)

    def _load(self, compileState: CompileState, stack: Optional[ScoreboardValue], scale=1) -> ScoreboardValue:
        stack = stack or compileState.expressionStack.next()

        # ToDo missing scale
        compileState.ir.append(StoreFastVarNode(
            stack,
            self.value
        ))

        return stack

    def _copy(self, compileState: CompileState, target: ValueResource) -> ValueResource:
        if not isinstance(target, NbtAddressResource):
            if isinstance(target, AddressResource):
                return self.load(compileState, target)
            raise ValueError(f"{type(self).__name__} expected NbtAddressResource, got {repr(target)}")

        compileState.ir.append(StoreFastVarNode(
            target.value,
            self.value
        ))
        return target

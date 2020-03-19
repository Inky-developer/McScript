from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.data.Commands import BinaryOperator
from src.mcscript.lang.Protocols.binaryOperatorProtocols import BinaryOperatorProtocol
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import ValueResource, Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class BooleanResource(ValueResource, BinaryOperatorProtocol):
    """
    Holds a boolean
    """

    def numericOperation(self, other: ValueResource, operator: BinaryOperator, compileState: CompileState) -> Resource:
        return self.convertToNumber(compileState).numericOperation(other, operator, compileState)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.BOOLEAN

    def embed(self) -> str:
        return str(int(self.value)) if self.isStatic else str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, (int, bool))

    def convertToNumber(self, compileState) -> NumberResource:
        return NumberResource(self.value if not self.isStatic else int(self.value), self.isStatic)

    def convertToFixedNumber(self, compileState) -> FixedNumberResource:
        return self.convertToNumber(compileState).convertToFixedNumber(compileState)

    def toNumber(self) -> int:
        if self.isStatic:
            return int(self.value)
        raise TypeError

    def storeToNbt(self, stack: AddressResource, compileState: CompileState) -> ValueResource:
        return self.convertToNumber(compileState).storeToNbt(stack, compileState)

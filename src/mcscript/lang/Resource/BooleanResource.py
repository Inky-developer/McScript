from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.data.Commands import BinaryOperator, Command, Struct
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.NbtAddressResource import NbtAddressResource
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import ValueResource, Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.utils.utils import deprecated

if TYPE_CHECKING:
    from src.mcscript import CompileState


class BooleanResource(ValueResource):
    """
    Holds a boolean
    """

    requiresInlineFunc = False

    TRUE: BooleanResource
    FALSE: BooleanResource

    @deprecated("Boolean arithmetic expression will be removed when boolean operators get implemented")
    def numericOperation(self, other: ValueResource, operator: BinaryOperator, compileState: CompileState) -> Resource:
        return self.convertToNumber(compileState).numericOperation(other, operator, compileState)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.BOOLEAN

    def embed(self) -> str:
        return ("true" if self.value else "false") if self.isStatic else str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, (int, bool))

    def convertToNumber(self, compileState) -> NumberResource:
        return NumberResource(self.value if not self.isStatic else int(self.value), self.isStatic)

    def convertToFixedNumber(self, compileState) -> FixedNumberResource:
        return self.convertToNumber(compileState).convertToFixedNumber(compileState)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self

    def toNumber(self) -> int:
        if self.isStatic:
            return int(self.value)
        raise TypeError

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> ValueResource:
        from src.mcscript.lang.Resource.BooleanVariableResource import BooleanVariableResource

        if self.hasStaticValue:
            compileState.writeline(Command.SET_VARIABLE(
                address=stack.address,
                struct=Struct.VAR(var=stack.name, value=int(self))
            ))
        else:
            compileState.writeline(Command.SET_VARIABLE_FROM(
                var=stack,
                command=Command.GET_SCOREBOARD_VALUE(stack=str(self))
            ))
        return BooleanVariableResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        if not isinstance(target, AddressResource):
            if isinstance(target, NbtAddressResource):
                # convert this to a variable at the given path
                return self.storeToNbt(target, compileState)
            raise RuntimeError(f"BooleanResource uses AddressResource, got {repr(target)}")
        if self.isStatic:
            compileState.writeline(Command.SET_VALUE(
                stack=target,
                value=self.value
            ))
        else:
            compileState.writeline(Command.SET_VALUE_FROM(
                stack=target,
                command=Command.GET_SCOREBOARD_VALUE(
                    stack=self.value
                )
            ))
        return BooleanResource(target, False)

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> Resource:
        from src.mcscript.lang.Resource.BooleanVariableResource import BooleanVariableResource
        return compileState.currentNamespace().addVar(identifier, BooleanVariableResource)


BooleanResource.TRUE = BooleanResource(1, True)
BooleanResource.FALSE = BooleanResource(0, True)

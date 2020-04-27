from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import BinaryOperator, Command, ConditionalExecute, Relation, Struct
from mcscript.data.commandsCommon import compare_scoreboard_value
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.utils import deprecated

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


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
        from mcscript.lang.resource.BooleanVariableResource import BooleanVariableResource

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

    def operation_test_relation(self, compileState: CompileState, relation: Relation,
                                other: Resource) -> ConditionalExecute:
        if relation not in (Relation.EQUAL, Relation.NOT_EQUAL):
            raise TypeError

        other = other.load(compileState)
        if not isinstance(other, BooleanResource):
            raise TypeError

        return compare_scoreboard_value(compileState, self, relation, other)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        if not isinstance(target, AddressResource):
            if isinstance(target, NbtAddressResource):
                # convert this to a variable at the given path
                return self.storeToNbt(target, compileState)
            raise ValueError(f"BooleanResource uses AddressResource, got {repr(target)}")
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
        from mcscript.lang.resource.BooleanVariableResource import BooleanVariableResource
        return compileState.currentNamespace().addVar(identifier, BooleanVariableResource)


BooleanResource.TRUE = BooleanResource(1, True)
BooleanResource.FALSE = BooleanResource(0, True)

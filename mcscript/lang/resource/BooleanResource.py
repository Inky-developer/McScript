from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commandsCommon import compare_scoreboard_value
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class BooleanResource(ValueResource):
    """
    Holds a boolean
    """

    requiresInlineFunc = False

    TRUE: BooleanResource
    FALSE: BooleanResource

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.BOOLEAN

    def embed(self) -> str:
        return ("true" if self.static_value else "false") if self.isStatic else str(self.static_value)

    def typeCheck(self) -> bool:
        return isinstance(self.static_value, (int, bool))

    def convertToNumber(self, compileState) -> NumberResource:
        return NumberResource(self.static_value if not self.isStatic else int(self.static_value), self.isStatic)

    def convertToFixedNumber(self, compileState) -> FixedNumberResource:
        return self.convertToNumber(compileState).convertToFixedNumber(compileState)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return self

    def toNumber(self) -> int:
        if self.isStatic:
            return int(self.static_value)
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
        other = other.convertToNumber(compileState)

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
                value=self.static_value
            ))
        else:
            compileState.writeline(Command.SET_VALUE_FROM(
                stack=target,
                command=Command.GET_SCOREBOARD_VALUE(
                    stack=self.static_value
                )
            ))
        return BooleanResource(target, False)

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> Resource:
        from mcscript.lang.resource.BooleanVariableResource import BooleanVariableResource
        return BooleanVariableResource(compileState.get_nbt_address(identifier), False)


BooleanResource.TRUE = BooleanResource(True, True)
BooleanResource.FALSE = BooleanResource(False, True)

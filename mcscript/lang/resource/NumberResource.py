from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.ir.command_components import BinaryOperator
from mcscript.ir.components import FastVarOperationNode, StoreVarNode, StoreFastVarNode
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.lang.resource.NumberVariableResource import NumberVariableResource
    from mcscript.lang.resource.BooleanResource import BooleanResource


class NumberResource(ValueResource):
    """
    Holds a Number(int)
    """

    requiresInlineFunc = False

    @staticmethod
    def type():
        return ResourceType.NUMBER

    def embed(self) -> str:
        return str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, int)

    def convertToNumber(self, compileState: CompileState) -> NumberResource:
        return self

    def convertToFixedNumber(self, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic:
            return FixedNumberResource.fromNumber(self.value)

        compileState.ir.append(FastVarOperationNode(
            self.value,
            compileState.getConstant(FixedNumberResource.BASE),
            BinaryOperator.TIMES
        ))

        return FixedNumberResource(self.value, False)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        """ return True if the value of this resource does not match 0"""
        from mcscript.lang.resource.BooleanResource import BooleanResource
        if self.isStatic:
            return BooleanResource.FALSE if self.value == 0 else BooleanResource.TRUE

        # stack = compileState.expressionStack.next()
        # compileState.writeline(Command.SET_VALUE(
        #     stack=stack,
        #     value=1
        # ))
        # compileState.writeline(Command.EXECUTE(
        #     sub=ExecuteCommand.IF_SCORE_RANGE(
        #         stack=self.value,
        #         range=0
        #     ),
        #     command=Command.SET_VALUE(
        #         stack=stack,
        #         value=0
        #     )
        # ))
        return BooleanResource(self.value, False)

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> NumberVariableResource:
        """ Load a number from a scoreboard (NumberResource) to a data storage"""
        from mcscript.lang.resource.NumberVariableResource import NumberVariableResource

        compileState.ir.append(StoreVarNode(
            stack.value,
            self.value
        ))

        return NumberVariableResource(stack, False)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        # ToDo: refactor
        if not isinstance(target, AddressResource):
            if isinstance(target, NbtAddressResource):
                # convert this to a variable at the given path
                return self.storeToNbt(target, compileState)
            raise ValueError(f"NumberResource uses AddressResource, got {repr(target)}")
        compileState.ir.append(StoreFastVarNode(
            target.value,
            self.value
        ))

        return NumberResource(target, False)

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> Resource:
        from mcscript.lang.resource.NumberVariableResource import NumberVariableResource
        return compileState.currentContext().add_var(
            identifier,
            NumberVariableResource(compileState.get_nbt_address(identifier), False)
        )

    def _numericOperationStatic(self, first: int, second: int, operator: BinaryOperator) -> NumberResource:
        actions = {
            BinaryOperator.PLUS: lambda a, b: a + b,
            BinaryOperator.MINUS: lambda a, b: a - b,
            BinaryOperator.TIMES: lambda a, b: a * b,
            BinaryOperator.DIVIDE: lambda a, b: a // b,
            BinaryOperator.MODULO: lambda a, b: a % b
        }
        return NumberResource(actions[operator](first, second), True)

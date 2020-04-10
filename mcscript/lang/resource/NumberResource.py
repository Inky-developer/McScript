from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptTypeError
from mcscript.data.commands import Command, BinaryOperator, multiple_commands, Struct, ExecuteCommand
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import ValueResource, Resource
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

    def numericOperation(self, other: ValueResource, operator: BinaryOperator,
                         compileState: CompileState) -> NumberResource:
        if self.isStatic and other.isStatic:
            try:
                value = int(other)
            except TypeError:
                raise McScriptTypeError(f"Cannot do the operation '{self} {operator.value} {other}' "
                                        f"where the second value can't be converted to a number", compileState)
            return self._numericOperationStatic(int(self), value, operator)
        return self._numericOperation(other, operator, compileState)

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
        # else multiply this value by the factor
        stack = compileState.expressionStack.next()
        compileState.writeline(multiple_commands(
            Command.SET_VALUE(stack=stack, value=FixedNumberResource.BASE),
            Command.OPERATION(stack=self.value, operator=BinaryOperator.TIMES.value, stack2=stack)
        ))

        # remove the previous stack
        compileState.expressionStack.previous()
        return FixedNumberResource(self.value, False)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        """ return True if the value of this resource does not match 0"""
        from mcscript.lang.resource.BooleanResource import BooleanResource
        if self.isStatic:
            return BooleanResource.FALSE if self.value == 0 else BooleanResource.TRUE

        stack = compileState.expressionStack.next()
        compileState.writeline(Command.SET_VALUE(
            stack=stack,
            value=1
        ))
        compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=self.value,
                range=0
            ),
            command=Command.SET_VALUE(
                stack=stack,
                value=0
            )
        ))
        return BooleanResource(stack, False)

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> NumberVariableResource:
        """ Load a number from a scoreboard (NumberResource) to a scoreboard (this)"""
        from mcscript.lang.resource.NumberVariableResource import NumberVariableResource

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
        return NumberVariableResource(stack, False)

    def operation_negate(self, compileState: CompileState) -> Resource:
        if self.isStatic:
            return NumberResource(-self.value, True)

        tmp = compileState.expressionStack.next()
        compileState.writeline(multiple_commands(
            Command.SET_VALUE(
                stack=tmp,
                value=-1
            ),
            Command.OPERATION(
                stack=self.value,
                operator=BinaryOperator.TIMES.value,
                stack2=tmp
            )
        ))
        compileState.expressionStack.previous()
        return NumberResource(self.value, False)

    def _numericOperation(self, other: ValueResource, operator: BinaryOperator,
                          compileState: CompileState) -> NumberResource:
        try:
            other = other.convertToNumber(compileState)
        except TypeError:
            raise McScriptTypeError(f"Cannot do the operation with a value that can't be converted to a number",
                                    compileState)
        if self.isStatic:
            stack1 = compileState.expressionStack.next()
            compileState.writeline(Command.SET_VALUE(stack=stack1, value=self.value))
        elif other.isStatic and operator in (BinaryOperator.PLUS, BinaryOperator.MINUS):
            # if this not static but the other variable is,
            # use the special 'scoreboard players add/remove' syntax if possible
            return self._numericOperationSpecialAdd(other.value if operator == operator.PLUS else -other.value,
                                                    compileState)
        else:
            stack1 = self.value

        otherStack = False
        if other.isStatic:
            stack2 = compileState.expressionStack.next()
            compileState.writeline(Command.SET_VALUE(stack=stack2, value=int(other)))
            otherStack = True
        else:
            stack2 = other.value

        compileState.writeline(Command.OPERATION(
            stack=stack1,
            operator=operator.value,
            stack2=stack2
        ))

        # the last expression is not needed anymore
        if otherStack:
            compileState.expressionStack.previous()
        return NumberResource(stack1, False)

    def copy(self, target: ValueResource, compileState: CompileState) -> Resource:
        if not isinstance(target, AddressResource):
            if isinstance(target, NbtAddressResource):
                # convert this to a variable at the given path
                return self.storeToNbt(target, compileState)
            raise ValueError(f"NumberResource uses AddressResource, got {repr(target)}")
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
        return NumberResource(target, False)

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> Resource:
        from mcscript.lang.resource.NumberVariableResource import NumberVariableResource
        return compileState.currentNamespace().addVar(identifier, NumberVariableResource)

    # noinspection PyShadowingNames
    def _numericOperationStatic(self, a: int, b: int, operator: BinaryOperator) -> NumberResource:
        actions = {
            BinaryOperator.PLUS: lambda a, b: a + b,
            BinaryOperator.MINUS: lambda a, b: a - b,
            BinaryOperator.TIMES: lambda a, b: a * b,
            BinaryOperator.DIVIDE: lambda a, b: a // b,
            BinaryOperator.MODULO: lambda a, b: a % b
        }
        return NumberResource(actions[operator](a, b), True)

    def _numericOperationSpecialAdd(self, b: int, compileState: CompileState) -> NumberResource:
        command = Command.ADD_SCORE if b > 0 else Command.REMOVE_SCORE
        compileState.writeline(command(stack=str(self), value=abs(b)))
        return self

from __future__ import annotations

from typing import Dict, TYPE_CHECKING, Union

from mcscript.data.commandsCommon import compare_scoreboard_value
from mcscript.exceptions.compileExceptions import McScriptTypeError
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.lang.resource.BooleanResource import BooleanResource
    from mcscript.lang.resource.NumberResource import NumberResource
    from mcscript.compiler.CompileState import CompileState
    from mcscript.lang.resource.FixedNumberVariableResource import FixedNumberVariableResource


class FixedNumberResource(ValueResource):
    """
    A Fixed number: used for calculations with rational numbers.
    The current precision is not great (1/1024) and the number should be kept as small as possible
    Edit: maybe the lower precision of 1 / 1000 is better, since the amount values that can be expressed exactly
    is usually better.
    Behavior:
        - if both numbers are static, do the entire operation statically
        - if one of the numbers is static, do the entire operation as no number was static
        - operations with other fixed numbers will produce fixed numbers
        - operations with other values will call toFixed of that resource and then do the operation
    """

    BASE = 1000

    requiresInlineFunc = False

    def embed(self) -> str:
        return str("{}d".format(self.static_value / self.BASE) if self.isStatic else self.static_value)

    def typeCheck(self) -> bool:
        return isinstance(self.static_value, int)

    def toTextJson(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Dict:
        if self.isStatic:
            return formatter.createFromResource(self.embed())

        return formatter.createFromResource(self.storeToNbt(
            NbtAddressResource(compileState.temporaryStorageStack.next().embed()), compileState))

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.FIXED_POINT

    @classmethod
    def fromNumber(cls, number: Union[int, float]) -> FixedNumberResource:
        return FixedNumberResource(int(round(number * cls.BASE)), True)

    def convertToNumber(self, compileState: CompileState) -> NumberResource:
        from mcscript.lang.resource.NumberResource import NumberResource
        if self.isStatic:
            return NumberResource(self.static_value // self.BASE, True)

        tmpStack = compileState.getConstant(self.BASE)
        compileState.writeline(Command.OPERATION(
            stack=self.static_value,
            operator=BinaryOperator.DIVIDE.value,
            stack2=tmpStack
        ))
        return NumberResource(self.static_value, False)

    def convertToFixedNumber(self, compileState: CompileState) -> FixedNumberResource:
        return self

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        """ return True if the value of this resource does not match 0"""
        from mcscript.lang.resource.BooleanResource import BooleanResource
        if self.isStatic:
            return BooleanResource.FALSE if self.static_value == 0 else BooleanResource.TRUE

        stack = compileState.expressionStack.next()
        compileState.writeline(Command.SET_VALUE(
            stack=stack,
            value=1
        ))
        compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=self.static_value,
                range=0
            ),
            command=Command.SET_VALUE(
                stack=stack,
                value=0
            )
        ))
        return BooleanResource(stack, False)

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> FixedNumberVariableResource:
        from mcscript.lang.resource.FixedNumberVariableResource import FixedNumberVariableResource

        if self.isStatic:
            compileState.writeline(Command.SET_VARIABLE(
                address=stack.address,
                struct=Struct.VAR(
                    var=stack.name,
                    value=f"{self.value / self.BASE}d"
                )))
        else:
            compileState.writeline(
                Command.SET_VARIABLE_FROM(
                    var=stack,
                    scale=1 / self.BASE,
                    type=Type.DOUBLE,
                    command=Command.GET_SCOREBOARD_VALUE(stack=self.static_value)
                )
            )
        return FixedNumberVariableResource(stack, False)

    def operation_test_relation(self, compileState: CompileState, relation: Relation,
                                other: Resource) -> ConditionalExecute:
        other = other.convertToFixedNumber(compileState)
        if not isinstance(other, ValueResource):
            raise TypeError

        if isinstance(other, FixedNumberResource):
            return compare_scoreboard_value(compileState, self, relation, other)

    def operation_plus(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.static_value + other.value, True)

        a, b = self, other
        if a.isStatic:
            a, b = b, a

        # if one of the values is static, just do scoreboard players add
        if b.isStatic:
            command = Command.ADD_SCORE if b.value >= 0 else Command.REMOVE_SCORE
            compileState.writeline(command(stack=a.static_value, value=abs(b.value)))
            return a

        # else do a normal operation
        compileState.writeline(Command.OPERATION(
            stack=a.static_value,
            operator=BinaryOperator.PLUS.value,
            stack2=b.value
        ))
        return a

    def operation_minus(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.static_value - other.value, True)
        a, b = self, other
        if a.isStatic:
            a, b = b, a

        # if one of the values is static, just do scoreboard players add
        if b.isStatic:
            command = Command.ADD_SCORE if b.value <= 0 else Command.REMOVE_SCORE
            compileState.writeline(command(stack=a.static_value, value=abs(b.value)))
            return a

        # else do a normal operation
        compileState.writeline(Command.OPERATION(
            stack=a.static_value,
            operator=BinaryOperator.MINUS.value,
            stack2=b.value
        ))
        return a

    def operation_times(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.static_value * other.value // self.BASE, True)

        # 1. a *= b
        # 2. a += base // 2 (for correct rounding, round(a) = int(a+0.5)), rounding not implemented for now(performance)
        # 3. c = base
        # 4. a /= c

        b = other.toScoreboard(compileState) if not other.isStatic else compileState.getConstant(other.value)
        a = self.toScoreboard(compileState)

        tmpStack = compileState.getConstant(self.BASE)
        compileState.writeline(multiple_commands(
            Command.OPERATION(
                stack=a.static_value,
                operator=BinaryOperator.TIMES.value,
                stack2=b.value
            ),
            # Command.ADD_SCORE(
            #     stack=a.value,
            #     value=self.BASE // 2
            # ),
            Command.OPERATION(
                stack=a.static_value,
                operator=BinaryOperator.DIVIDE.value,
                stack2=tmpStack
            )
        ))

        return a

    def operation_divide(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.static_value * self.BASE // other.value, True)

        commands = []

        if self.isStatic:
            a = FixedNumberResource(self.static_value * self.BASE, True).toScoreboard(compileState)
        else:
            a = self.toScoreboard(compileState)
            commands.append(Command.OPERATION(
                stack=a.static_value,
                operator=BinaryOperator.TIMES.value,
                stack2=compileState.getConstant(self.BASE)
            ))

        if other.isStatic:
            b = compileState.compilerConstants.get_constant(other.value)
            commands.append(Command.OPERATION(
                stack=a.static_value,
                operator=BinaryOperator.DIVIDE.value,
                stack2=b
            ))
        else:
            b = other.toScoreboard(compileState)
            commands.append(Command.OPERATION(
                stack=a.static_value,
                operator=BinaryOperator.DIVIDE.value,
                stack2=b.value
            ))

        compileState.writeline(multiple_commands(*commands))

        return FixedNumberResource(a.static_value, False)

    def operation_modulo(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.isStatic and other.isStatic:
            return FixedNumberResource(self.static_value % other.value, True)

        a = self.toScoreboard(compileState)
        b = other.toScoreboard(compileState)

        compileState.writeline(Command.OPERATION(
            stack=a,
            operator=BinaryOperator.MODULO.value,
            stack2=b
        ))
        return a

    def operation_negate(self, compileState: CompileState) -> Resource:
        if self.hasStaticValue:
            return FixedNumberResource(-self.static_value, True)

        # else multiply this by -1
        compileState.writeline(multiple_commands(
            Command.OPERATION(
                stack=self.embed(),
                operator=BinaryOperator.TIMES.value,
                stack2=compileState.getConstant(-1)
            )
        ))
        compileState.expressionStack.previous()
        return FixedNumberResource(self.static_value, False)

    def toScoreboard(self, compileState) -> FixedNumberResource:
        if not self.isStatic:
            return self

        stack = compileState.expressionStack.next()
        compileState.writeline(Command.SET_VALUE(stack=stack, value=self.static_value))
        return FixedNumberResource(stack, False)

    def toNumber(self) -> int:
        # is this really what should happen?
        # update comparisons for custom implementations
        if self.isStatic:
            return self.static_value
        raise TypeError

    def checkOtherOperator(self, other: ValueResource, compileState: CompileState) -> FixedNumberResource:
        if hasattr(other, "convertToFixedNumber"):
            return other.convertToFixedNumber(compileState)

        raise McScriptTypeError(f"Expected a type that can be converted to a fixed point number but got {repr(other)}",
                                compileState)

    def copy(self, target: ValueResource, compileState: CompileState) -> ValueResource:
        if not isinstance(target, AddressResource):
            if isinstance(target, NbtAddressResource):
                # convert this to a variable at the given path
                return self.storeToNbt(target, compileState)
            raise ValueError(f"FixedNumberResource uses AddressResource, got {repr(target)}")
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
        return FixedNumberResource(target, False)

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> Resource:
        from mcscript.lang.resource.FixedNumberVariableResource import FixedNumberVariableResource
        return compileState.currentContext().add_var(identifier, FixedNumberVariableResource(
            compileState.get_nbt_address(identifier), False
        ))

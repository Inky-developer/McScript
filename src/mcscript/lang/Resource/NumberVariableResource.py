from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.data.Commands import Command, BinaryOperator
from src.mcscript.lang.Protocols.unaryOperatorProtocols import ExplicitUnaryNumberVariableOperationProtocol
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript.compiler.CompileState import CompileState


class NumberVariableResource(ValueResource, ExplicitUnaryNumberVariableOperationProtocol):
    """
    Used when a number is stored as a variable
    """
    _hasStaticValue = False
    isDefault = False

    def embed(self) -> str:
        return str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, AddressResource) and not self.isStatic

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NUMBER

    def load(self, compileState: CompileState) -> NumberResource:
        stack = compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_VARIABLE(
            stack=stack,
            var=self.embed()
        ))
        return NumberResource(stack, False)

    def operation_increment_one(self, compileState: CompileState) -> NumberVariableResource:
        # 1. load self
        # 2. increment scoreboard value
        # 3. store back
        number = self.load(compileState)
        number = number.numericOperation(NumberResource(1, True), BinaryOperator.PLUS, compileState)
        return number.storeToNbt(self.value, compileState)

    def operation_decrement_one(self, compileState: CompileState) -> NumberVariableResource:
        # 1. load self
        # 2. increment scoreboard value
        # 3. store back
        number = self.load(compileState)
        number = number.numericOperation(NumberResource(1, True), BinaryOperator.MINUS, compileState)
        return number.storeToNbt(self.value, compileState)

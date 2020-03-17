from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.mcscript.data.Commands import Operator
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource

if TYPE_CHECKING:
    from src.mcscript import CompileState


class NumberProtocol(ABC):
    @abstractmethod
    def numericOperation(self, other: ValueResource, operator: Operator, compileState: CompileState) -> Resource:
        pass


class ExplicitNumberProtocol(NumberProtocol, ABC):
    """
    Simplified NumberProtocol if every operand must be implemented.
    """

    def numericOperation(self, other: ValueResource, operator: Operator, compileState: CompileState) -> Resource:
        other = self._checkOther(other, compileState)
        if operator == Operator.PLUS:
            return self.operation_plus(other, compileState)
        elif operator == Operator.MINUS:
            return self.operation_minus(other, compileState)
        elif operator == Operator.TIMES:
            return self.operation_times(other, compileState)
        elif operator == Operator.DIVIDE:
            return self.operation_divide(other, compileState)
        elif operator == Operator.MODULO:
            return self.operation_modulo(other, compileState)
        raise ValueError("Unknown operator: " + repr(operator))

    def _checkOther(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        """
        Called before an operation to convert the operator to a more fitting type
        :param other: the other value
        """
        return other

    @abstractmethod
    def operation_plus(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        pass

    @abstractmethod
    def operation_minus(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        pass

    @abstractmethod
    def operation_times(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        pass

    @abstractmethod
    def operation_divide(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        pass

    @abstractmethod
    def operation_modulo(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        pass

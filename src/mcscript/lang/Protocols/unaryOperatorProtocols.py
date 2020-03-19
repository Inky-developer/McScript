from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.mcscript.Exceptions import McScriptTypeError
from src.mcscript.data.Commands import UnaryOperator
from src.mcscript.lang.Resource.ResourceBase import Resource

if TYPE_CHECKING:
    from src.mcscript import CompileState


class UnaryNumberOperatorProtocol(ABC):
    @abstractmethod
    def unaryOperation(self, operator: UnaryOperator, compileState: CompileState) -> Resource:
        """
        Does a unary operation with this operator and returns the new resource
        :param operator: the operator
        :param compileState: the compile state
        :return: the new resource
        """


class ExplicitUnaryNumberOperationProtocol(UnaryNumberOperatorProtocol, ABC):
    def unaryOperation(self, operator: UnaryOperator, compileState: CompileState) -> Resource:
        try:
            if operator == UnaryOperator.MINUS:
                return self.operation_negate(compileState)
        except TypeError:
            raise McScriptTypeError(f"{repr(self)} Does not support the unary operation {operator.name}")

        raise ValueError(f"Unknown Operator {operator.name} for ExplicitUnaryOperationProtocol")

    @abstractmethod
    def operation_negate(self, compileState: CompileState) -> Resource:
        """
        Returns a resource whose value negated is the value of this resource
        :param compileState: the compileState
        :return: the new resource
        """


class UnaryNumberVariableOperatorProtocol(ABC):
    @abstractmethod
    def unaryOperation(self, operator: UnaryOperator, compileState: CompileState) -> Resource:
        """
        Does a unary operation with this operator and returns the new resource
        :param operator: the operator
        :param compileState: the compile state
        :return: the new resource
        """


class ExplicitUnaryNumberVariableOperationProtocol(UnaryNumberVariableOperatorProtocol, ABC):
    def unaryOperation(self, operator: UnaryOperator, compileState: CompileState) -> Resource:
        try:
            if operator == UnaryOperator.INCREMENT_ONE:
                return self.operation_increment_one(compileState)
            elif operator == UnaryOperator.DECREMENT_ONE:
                return self.operation_decrement_one(compileState)
        except TypeError:
            raise McScriptTypeError(f"{repr(self)} Does not support the unary operation {operator.name}")

        raise ValueError(f"Unknown Operator {operator.name} for ExplicitUnaryVariableOperationProtocol")

    @abstractmethod
    def operation_increment_one(self, compileState: CompileState) -> Resource:
        """
        Returns a resource which has the value +1 of this resource
        :param compileState: the compileState
        :return: the new resource
        """

    @abstractmethod
    def operation_decrement_one(self, compileState: CompileState) -> Resource:
        """
        Returns a resource which has the value of -1 of this resource
        :param compileState: the compileState
        :return: the new resource
        """

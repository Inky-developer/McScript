from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Dict

from mcscript.ir.command_components import BinaryOperator, ScoreRelation, ScoreRange
from mcscript.ir.components import FastVarOperationNode, StoreVarNode, StoreFastVarNode, FastVarOperationNode, ConditionalNode
from mcscript.lang.resource.AddressResource import AddressResource
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.resources import ScoreboardValue, DataPath
from mcscript.exceptions.compileExceptions import McScriptTypeError

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.lang.resource.NumberVariableResource import NumberVariableResource
    from mcscript.lang.resource.BooleanResource import BooleanResource


class NumberResource(ValueResource[int]):
    """
    Holds a Number(int)
    """

    requiresInlineFunc: ClassVar[bool] = False

    @staticmethod
    def type():
        return ResourceType.NUMBER

    def store(self, compileState: CompileState) -> NumberResource:
        """ Load a static number to a scoreboard or to a data storage """
        if not self.is_static:
            return NumberResource(self.static_value, self.scoreboard_value)

        scoreboard_address = compileState.expressionStack.next()
        compileState.ir.append(StoreFastVarNode(
            scoreboard_address, self.static_value, self.is_static
        ))

        return NumberResource(self.static_value, scoreboard_address)

    def copy(self, target: ScoreboardValue, compileState: CompileState) -> Resource:
        # Just write the static value if available, otherwise copy from own scoreboard value
        own_value = self.static_value or self.scoreboard_value

        compileState.ir.append(StoreFastVarNode(
            target,
            own_value,
            False
        ))

        return NumberResource(target, self.static_value)

    def numericOperation(self, other: ValueResource, operator: BinaryOperator, compileState: CompileState) -> NumberResource:
        if not isinstance(other, NumberResource):
            raise TypeError()

        if self.static_value is not None and other.static_value is not None:
            return self._numericOperationStatic(self.static_value, other.static_value, operator)

        # Most performance: performing the operation with a scoreboard value
        # as the first operand and a static value as the seconds operand
        # As a non static first operand is not possible and would have to be stored
        a, b = self.scoreboard_value, other.static_value or other.scoreboard_value

        # if this is a static variable, create a scoreboard entry and modify that
        if self.is_static:
            a = self.store(compileState).scoreboard_value

        compileState.ir.append(
            FastVarOperationNode(
                a,
                b,
                operator
            )
        )

        return NumberResource(None, a)

    def operation_test_relation(self, compile_state: CompileState, relation: ScoreRelation, other: Resource) -> ConditionalNode:        
        if not isinstance(other, NumberResource):
            raise TypeError()
        
        a, b = self, other
        if a.is_static:
            a, b = b, a
            relation = relation.swap()

        if a is b:
            node = ConditionalNode.IfBool(relation in 
                (ScoreRelation.EQUAL, ScoreRelation.GREATER_OR_EQUAL, ScoreRelation.LESS_OR_EQUAL)
            )
        elif a.is_static:
            node = ConditionalNode.IfBool(relation.apply(self.static_value, other.static_value))
        elif b.is_static:
            score_range, invert = relation.get_score_range(b.static_value)
            node = ConditionalNode.IfScoreMatches(
                a.scoreboard_value, 
                score_range,
                invert
            )
        else:
            node = ConditionalNode.IfScore(
                a.scoreboard_value,
                b.scoreboard_value,
                relation
            )
        
        return ConditionalNode([node])

    def __int__(self) -> int:
        if self.static_value is not None:
            return self.static_value
        return NotImplemented

    def _numericOperationStatic(self, first: int, second: int, operator: BinaryOperator) -> NumberResource:
        actions = {
            BinaryOperator.PLUS: lambda a, b: a + b,
            BinaryOperator.MINUS: lambda a, b: a - b,
            BinaryOperator.TIMES: lambda a, b: a * b,
            BinaryOperator.DIVIDE: lambda a, b: a // b,
            BinaryOperator.MODULO: lambda a, b: a % b
        }
        return NumberResource(actions[operator](first, second), None)

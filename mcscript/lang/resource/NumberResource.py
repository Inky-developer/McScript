from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from mcscript.ir.command_components import BinaryOperator, ScoreRelation
from mcscript.ir.components import StoreFastVarNode, ConditionalNode
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.utility import operate_scoreboard_values, compare_scoreboard_values

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class NumberResource(ValueResource[int]):
    """
    Holds a Number(int)
    """

    requiresInlineFunc: ClassVar[bool] = False

    @staticmethod
    def type():
        return ResourceType.INTEGER

    def store(self, compileState: CompileState) -> NumberResource:
        """ Load a static number to a scoreboard or to a data storage """
        if not self.is_static:
            return NumberResource(self.static_value, self.scoreboard_value)

        scoreboard_address = compileState.expressionStack.next()
        compileState.ir.append(StoreFastVarNode(scoreboard_address, self.static_value))

        return NumberResource(self.static_value, scoreboard_address)

    def numericOperation(self, other: ValueResource, operator: BinaryOperator,
                         compileState: CompileState) -> NumberResource:
        if not isinstance(other, NumberResource):
            raise TypeError()

        result = operate_scoreboard_values(compileState, self, other, operator)
        if isinstance(result, int):
            return NumberResource(result, None)
        return NumberResource(None, result)

    def operation_test_relation(self, compile_state: CompileState, relation: ScoreRelation,
                                other: Resource) -> ConditionalNode:
        if not isinstance(other, NumberResource):
            raise TypeError()

        return compare_scoreboard_values(self, other, relation)

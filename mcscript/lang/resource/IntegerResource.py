from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from mcscript.ir.command_components import BinaryOperator, ScoreRelation
from mcscript.ir.components import StoreFastVarNode, ConditionalNode
from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import Int
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.utility import operate_scoreboard_values, compare_scoreboard_values

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class IntegerResource(ValueResource[int]):
    """
    Holds a Number(int)
    """

    requiresInlineFunc: ClassVar[bool] = False

    def type(self) -> Type:
        return Int

    def store(self, compileState: CompileState) -> IntegerResource:
        """ Load a static number to a scoreboard or to a data storage """
        if not self.is_static:
            return IntegerResource(self.static_value, self.scoreboard_value)

        scoreboard_address = compileState.expressionStack.next()
        compileState.ir.append(StoreFastVarNode(scoreboard_address, self.static_value))

        return IntegerResource(None, scoreboard_address)

    def numericOperation(self, other: ValueResource, operator: BinaryOperator,
                         compileState: CompileState) -> IntegerResource:
        if not isinstance(other, IntegerResource):
            raise TypeError()

        result = operate_scoreboard_values(compileState, self, other, operator)
        if isinstance(result, int):
            return IntegerResource(result, None)
        return IntegerResource(None, result)

    def operation_test_relation(self, compile_state: CompileState, relation: ScoreRelation,
                                other: Resource) -> ConditionalNode:
        if not isinstance(other, IntegerResource):
            raise TypeError()

        return compare_scoreboard_values(self, other, relation)

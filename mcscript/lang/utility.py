from __future__ import annotations

from typing import TYPE_CHECKING, Union

from mcscript.ir.command_components import ScoreRelation, BinaryOperator
from mcscript.ir.components import ConditionalNode, FastVarOperationNode
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.utils.resources import ScoreboardValue

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


def isStatic(resource: Resource) -> bool:
    """ Returns whether the resource is static if it is a value resource else False"""
    return getattr(resource, "isStatic", False)


def compare_scoreboard_values(a: ValueResource, b: ValueResource, relation: ScoreRelation):
    if a.is_static:
        a, b = b, a
        relation = relation.swap()

    if a is b:
        node = ConditionalNode.IfBool(
            relation in (ScoreRelation.EQUAL, ScoreRelation.GREATER_OR_EQUAL, ScoreRelation.LESS_OR_EQUAL))
    elif a.is_static:
        node = ConditionalNode.IfBool(relation.apply(a.static_value, b.static_value))
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


def operate_scoreboard_values(compile_state: CompileState, a: ValueResource, b: ValueResource,
                              operator: BinaryOperator) -> Union[int, ScoreboardValue]:
    # noinspection PyShadowingNames
    def numeric_operation_static(a: int, b: int, operator: BinaryOperator) -> int:
        actions = {
            BinaryOperator.PLUS: lambda first, second: first + second,
            BinaryOperator.MINUS: lambda first, second: first - second,
            BinaryOperator.TIMES: lambda first, second: first * second,
            BinaryOperator.DIVIDE: lambda first, second: first // second,
            BinaryOperator.MODULO: lambda first, second: first % second
        }
        return actions[operator](a, b)

    if a.is_static and b.is_static:
        return numeric_operation_static(a.static_value, b.static_value, operator)

    # Most performance: performing the operation with a scoreboard value
    # as the first operand and a static value as the seconds operand
    # As a non static first operand is not possible and would have to be stored
    a, b = a.scoreboard_value or a.store(compile_state).scoreboard_value, b.static_value or b.scoreboard_value

    compile_state.ir.append(
        FastVarOperationNode(
            a,
            b,
            operator
        )
    )

    return a

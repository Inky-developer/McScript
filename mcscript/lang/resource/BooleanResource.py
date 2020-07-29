from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.ir.command_components import ScoreRelation
from mcscript.ir.components import ConditionalNode

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class BooleanResource(ValueResource[bool]):
    """
    Holds a boolean
    """

    requiresInlineFunc = False

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.BOOLEAN

    def integer_value(self) -> int:
        if self.is_static:
            return int(self.static_value)
        raise TypeError

    def operation_test_relation(self, compileState: CompileState, relation: ScoreRelation,
                                other: Resource) -> ConditionalNode:
        if not isinstance(other, BooleanResource):
            raise TypeError()

        if relation not in (ScoreRelation.EQUAL, ScoreRelation.NOT_EQUAL):
            raise TypeError

        a, b = self, other

        if a.is_static:
            a, b = b, a
            relation = relation.swap()

        if a is b:
            node = ConditionalNode.IfBool(relation == ScoreRelation.EQUAL)
        elif a.is_static:
            node = ConditionalNode.IfBool(relation.apply(a.static_value, b.static_value))
        elif b.is_static:
            score_range, invert = relation.get_score_range(int(b.static_value))
            node = ConditionalNode.IfScoreMatches(a.scoreboard_value, score_range, invert)
        else:
            node = ConditionalNode.IfScore(a.scoreboard_value, b.scoreboard_value, relation)
        
        return ConditionalNode([node])

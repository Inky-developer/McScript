from __future__ import annotations

from typing import Dict, TYPE_CHECKING, Union, ClassVar

from mcscript.ir.command_components import StorageDataType, ScoreRelation, BinaryOperator
from mcscript.ir.components import (StoreVarFromResultNode, GetFastVarNode, ConditionalNode, FastVarOperationNode)
from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import Fixed
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.utility import compare_scoreboard_values, operate_scoreboard_values
from mcscript.utils.JsonTextFormat.objectFormatter import format_nbt

if TYPE_CHECKING:
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.compiler.CompileState import CompileState


class FixedNumberResource(ValueResource):
    """
    A Fixed number: used for calculations with rational numbers.
    The current precision is not great (1/1000) and the number should be kept as small as possible
    Behavior:
        - if both numbers are static, do the entire operation statically
        - if one of the numbers is static, do the entire operation as no number was static
        - operations with other fixed numbers will produce fixed numbers
        - operations with other values will call toFixed of that resource and then do the operation
    """

    BASE: ClassVar[int] = 1000

    def type(self) -> Type:
        return Fixed

    @classmethod
    def fromNumber(cls, number: Union[int, float]) -> FixedNumberResource:
        return FixedNumberResource(int(round(number * cls.BASE)), None)

    def operation_test_relation(self, compileState: CompileState, relation: ScoreRelation,
                                other: Resource) -> ConditionalNode:
        if not isinstance(other, FixedNumberResource):
            raise TypeError()
        return compare_scoreboard_values(self, other, relation)

    def operation_plus(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        value = operate_scoreboard_values(compileState, self, other, BinaryOperator.PLUS)
        if isinstance(value, int):
            return FixedNumberResource(value, None)
        return FixedNumberResource(None, value)

    def operation_minus(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        value = operate_scoreboard_values(compileState, self, other, BinaryOperator.MINUS)
        if isinstance(value, int):
            return FixedNumberResource(value, None)
        return FixedNumberResource(None, value)

    def operation_times(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.is_static and other.is_static:
            return FixedNumberResource(self.static_value * other.static_value // self.BASE, None)

        # 1. a *= b
        # 2. a += base // 2 (for correct rounding, round(a) = int(a+0.5)), rounding not implemented for now(performance)
        # 3. a /= base

        a, b = self, other

        if a.is_static:
            a, b = b, a

        # a is guaranteed to not be static at this point
        # Now multiply both values
        compileState.ir.append(FastVarOperationNode(
            a.scoreboard_value,
            b.static_value or b.scoreboard_value,
            BinaryOperator.TIMES
        ))

        # Consider using proper rounding or use an option for that
        # This code would do it:
        # compileState.ir.append(FastVarOperationNode(
        #     a.scoreboard_value,
        #     self.BASE // 2,
        #     BinaryOperator.PLUS
        # ))

        # and last divide by base
        compileState.ir.append(FastVarOperationNode(
            a.scoreboard_value,
            self.BASE,
            BinaryOperator.DIVIDE
        ))

        return FixedNumberResource(None, a.scoreboard_value)

    def operation_divide(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        if self.is_static and other.is_static:
            return FixedNumberResource(self.static_value * self.BASE // other.static_value, None)

        # 1. a *= base
        # 1.a. (for correct rounding) a += base
        # 2. a //= b

        a, b = self, other

        if a.is_static:
            # better dont swap operand while doing division...
            a = a.store(compileState)

        compileState.ir.append(FastVarOperationNode(
            a.scoreboard_value,
            self.BASE,
            BinaryOperator.TIMES
        ))

        compileState.ir.append(FastVarOperationNode(
            a.scoreboard_value,
            b.static_value or b.scoreboard_value,
            BinaryOperator.DIVIDE
        ))

        return FixedNumberResource(None, a.scoreboard_value)

    def operation_modulo(self, other: FixedNumberResource, compileState: CompileState) -> FixedNumberResource:
        value = operate_scoreboard_values(compileState, self, other, BinaryOperator.MODULO)
        if isinstance(value, int):
            return FixedNumberResource(value, None)
        return FixedNumberResource(None, value)

    def operation_negate(self, compileState: CompileState) -> Resource:
        if self.is_static:
            return FixedNumberResource(-self.static_value, None)

        compileState.ir.append(FastVarOperationNode(
            self.scoreboard_value,
            -1,
            BinaryOperator.TIMES
        ))
        return FixedNumberResource(self.static_value, self.scoreboard_value)

    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Dict:
        if self.is_static:
            return formatter.createFromResource(f"{self.static_value / self.BASE}")

        storage = compileState.temp_data_counter.next()
        compileState.ir.append(StoreVarFromResultNode(
            storage,
            GetFastVarNode(self.scoreboard_value),
            StorageDataType.DOUBLE,
            1 / self.BASE
        ))

        return format_nbt(storage)

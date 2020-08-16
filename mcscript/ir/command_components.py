from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple


class PositionKind(Enum):
    ABSOLUTE = auto()
    RELATIVE = auto()
    LOCAL = auto()


@dataclass()
class PositionAxis:
    value: float
    kind: PositionKind


@dataclass()
class Position:
    x: PositionAxis
    y: PositionAxis
    z: PositionAxis

    @staticmethod
    def with_kind(x: float, y: float, z: float, kind: PositionKind) -> Position:
        return Position(
            PositionAxis(x, kind),
            PositionAxis(y, kind),
            PositionAxis(z, kind)
        )

    @staticmethod
    def absolute(x: float, y: float, z: float) -> Position:
        return Position.with_kind(x, y, z, PositionKind.ABSOLUTE)

    @staticmethod
    def relative(x: float, y: float, z: float) -> Position:
        return Position.with_kind(x, y, z, PositionKind.RELATIVE)

    @staticmethod
    def local(x: float, y: float, z: float) -> Position:
        return Position.with_kind(x, y, z, PositionKind.LOCAL)


class ExecuteAnchor(Enum):
    FEET = "feet"
    EYES = "eyes"


class ScoreRelation(Enum):
    EQUAL = "=="
    NOT_EQUAL = "!="
    GREATER = ">"
    GREATER_OR_EQUAL = ">="
    LESS = "<"
    LESS_OR_EQUAL = "<="

    def swap(self) -> ScoreRelation:
        """
        swaps both values and returns the relation that is required to keep the value.

        >>> ScoreRelation.EQUAL.swap()
        <ScoreRelation.EQUAL: '=='>
        >>> ScoreRelation.GREATER.swap()
        <ScoreRelation.LESS: '<'>
        """
        if self == ScoreRelation.EQUAL:
            return ScoreRelation.EQUAL
        elif self == ScoreRelation.NOT_EQUAL:
            return ScoreRelation.NOT_EQUAL
        elif self == ScoreRelation.LESS:
            return ScoreRelation.GREATER
        elif self == ScoreRelation.LESS_OR_EQUAL:
            return ScoreRelation.GREATER_OR_EQUAL
        elif self == ScoreRelation.GREATER:
            return ScoreRelation.LESS
        elif self == ScoreRelation.GREATER_OR_EQUAL:
            return ScoreRelation.LESS_OR_EQUAL
        raise ValueError("What am I?")

    def apply(self, a, b) -> bool:
        """
        Returns whether this relation holds true for a and b
        Note: a and b must be comparable
        """
        if self == ScoreRelation.EQUAL:
            return a == b
        elif self == ScoreRelation.NOT_EQUAL:
            return a != b
        elif self == ScoreRelation.LESS:
            return a < b
        elif self == ScoreRelation.LESS_OR_EQUAL:
            return a <= b
        elif self == ScoreRelation.GREATER:
            return a > b
        elif self == ScoreRelation.GREATER_OR_EQUAL:
            return a >= b
        raise ValueError("What am I?")

    def get_score_range(self, a: int) -> Tuple[ScoreRange, bool]:
        """
        Returns a score range and a boolean
        The score range will contain every value 'x' for which:
        relation(x, a) is True.
        if the bool is set, the score range is inverted
        """
        if self == ScoreRelation.EQUAL:
            return ScoreRange(a), False
        elif self == ScoreRelation.NOT_EQUAL:
            return ScoreRange(a), True
        elif self == ScoreRelation.LESS:
            return ScoreRange(float("-inf"), a - 1), False
        elif self == ScoreRelation.LESS_OR_EQUAL:
            return ScoreRange(float("-inf"), a), False
        elif self == ScoreRelation.GREATER:
            return ScoreRange(a + 1, float("inf")), False
        elif self == ScoreRelation.GREATER_OR_EQUAL:
            return ScoreRange(a, float("inf")), False
        raise ValueError("What am I?")


class ScoreRange:
    def __init__(self, min_, max_=None):
        self.min = min_
        self.max = max_ or self.min

        if self.max < self.min:
            raise ValueError(f"The maximum value for range {self} must be greater than the minimum value")

    def __str__(self):
        if self.min == self.max:
            return str(int(self.min))

        return "{}..{}".format(str(int(self.min) if abs(self.min) != float("inf") else ""),
                               str(int(self.max) if abs(self.max) != float("inf") else ""))


class BinaryOperator(Enum):
    PLUS = "+"
    MINUS = "-"
    TIMES = "*"
    DIVIDE = "/"
    MODULO = "%"


class UnaryOperator(Enum):
    MINUS = "-"


class StorageDataType(Enum):
    BYTE = "byte"
    DOUBLE = "double"
    FLOAT = "float"
    LONG = "long"
    SHORT = "short"
    INT = "int"

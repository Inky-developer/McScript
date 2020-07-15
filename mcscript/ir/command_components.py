from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Set, List

from mcscript.data.Scoreboard import Scoreboard
from mcscript.utils.resourceSpecifier import ResourceSpecifier


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


class ExecuteAnchor(Enum):
    FEET = auto()
    EYES = auto()


class Identifier(str):
    allowed_identifiers: Set[str] = {chr(i) for i in range(ord('a'), ord('z') + 1)} \
                                    | {chr(i) for i in range(ord('A'), ord('Z') + 1)} \
                                    | {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'} \
                                    | {'_', '.', '-', '+'}

    def __new__(cls, content):
        for char in content:
            if char not in cls.allowed_identifiers:
                raise ValueError(f"Failed to create Identifier({content}): Character '{char}' is not allowed.\n"
                                 f"Use one of {list(sorted(cls.allowed_identifiers))}")
        # noinspection PyArgumentList
        return str.__new__(cls, content)


@dataclass()
class DataPath:
    storage: ResourceSpecifier
    path: List[str]


@dataclass()
class ScoreboardValue:
    value: Identifier
    scoreboard: Scoreboard


class ScoreRelation(Enum):
    EQUAL = "="
    NOT_EQUAL = "!="
    GREATER = ">"
    GREATER_OR_EQUAL = ">="
    LESS = "<"
    LESS_OR_EQUAL = "<="

    def swap(self) -> ScoreRelation:
        """
        swaps both values and returns the relation that is required to keep the value.

        Examples:
            a == b (=) b == a => Relation.EQUAL == Relation.EQUAL.swap()

            a <= b (=) b >= a => Relation.GREATER_OR_EQUAL == Relation.LESS_OR_EQUAL.swap()
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


class ScoreRange:
    def __init__(self, min_, max_=None):
        self.min = min_
        self.max = max_ or self.min

        if self.max < self.min:
            raise ValueError(f"The maximum value for range {self} must be greater than the minimum value")

    def __str__(self):
        if self.min == self.max:
            return str(int(self.min))

        return str(int(self.min) if abs(self.min) != float("inf") else "") \
               + ".." \
               + str(int(self.max) if abs(self.max) != float("inf") else "")


class BooleanOperator(Enum):
    PLUS = "+"
    MINUS = "-"
    TIMES = "*"
    DIVIDE = "/"
    MODULO = "%"

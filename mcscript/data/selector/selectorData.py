from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple

from mcscript.data import getResource


class Repeat(Enum):
    ZERO_OR_ONCE = auto()
    ZERO_OR_MORE = auto()


class Predicate(ABC):
    @abstractmethod
    def matches(self, other) -> bool:
        pass

    @classmethod
    def class_representation(cls) -> str:
        return cls.__name__


@dataclass(frozen=True)
class Range(Predicate):
    min: Optional[int]
    max: Optional[int]

    @classmethod
    def matches(cls, other) -> bool:
        return isinstance(other, cls) or isinstance(other, Integer)

    def __str__(self):
        return str(self.min or "") + ".." + str(self.max or "")


@dataclass(frozen=True)
class Identifier(Predicate):
    value: str

    @classmethod
    def matches(cls, other) -> bool:
        return isinstance(other, cls) or isinstance(other, String)

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Nbt(Predicate):
    raw_value: str

    @classmethod
    def matches(cls, other) -> bool:
        return isinstance(other, cls)

    def __str__(self):
        return self.raw_value


@dataclass(frozen=True)
class String(Predicate):
    value: str

    @classmethod
    def matches(cls, other) -> bool:
        return isinstance(other, cls)

    def __str__(self):
        return self.value


@dataclass(frozen=True)
class Literal(Predicate):
    options: Tuple[str]

    def class_representation(self) -> str:
        return str(self)

    def matches(self, other) -> bool:
        return isinstance(other, String) and other.value in self.options


@dataclass(frozen=True)
class Integer(Predicate):
    value: int

    @classmethod
    def matches(cls, other) -> bool:
        return isinstance(other, int)

    def __str__(self):
        return str(self.value)


SelectorValueType = Predicate

selectorString2Class = {
    "int": Integer,
    "range": Range,
    "identifier": Identifier,
    "string": String,
    "nbt": Nbt,
}


@dataclass(frozen=True)
class SelectorData:
    name: str
    accepts: SelectorValueType
    constant: bool
    repeat: Repeat
    priority: Tuple[int, int]


@dataclass(frozen=True)
class SelectorArgument:
    selector: SelectorData
    value: SelectorValueType
    negative: bool

    def __str__(self):
        return f"{self.selector.name}={'!' if self.negative else ''}{self.value}"


SELECTORS: Optional[List[SelectorData]] = None


def getSelectors() -> List[SelectorData]:
    assertLoaded()
    return SELECTORS


def getByName(name: str) -> SelectorData:
    assertLoaded()

    for selector in SELECTORS:
        if selector.name == name:
            return selector

    raise ValueError(f"Unknown selector: '{name}'")


def assertLoaded():
    global SELECTORS

    if SELECTORS is None:
        SELECTORS = []
        data = json.loads(getResource("SelectorArgs.json"))["selectors"]

        for selector in data:
            if selector["repeat"] == "?":
                repeat = Repeat.ZERO_OR_ONCE
            elif selector["repeat"] == "*":
                repeat = Repeat.ZERO_OR_MORE
            else:
                raise ValueError(f"Invalid repeat value\n{data}")

            accepts = selectorString2Class[selector["accepts"]] if not isinstance(selector["accepts"], list) else \
                Literal(tuple(selector["accepts"]))

            priority = selector["priority"], selector.get("priority_negated", selector["priority"])

            SELECTORS.append(SelectorData(
                selector["name"],
                accepts,
                selector["constant"],
                repeat,
                priority
            ))

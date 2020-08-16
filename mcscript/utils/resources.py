from __future__ import annotations

from dataclasses import dataclass
from typing import Set, List

from mcscript.utils.Scoreboard import Scoreboard


@dataclass(frozen=True)
class ResourceSpecifier:
    base: str
    path: str

    def __str__(self):
        return f"{self.base}:{self.path}"


class Identifier(str):
    allowed_identifiers: Set[str] = {chr(i) for i in range(ord('a'), ord('z') + 1)} \
                                    | {chr(i) for i in range(ord('A'), ord('Z') + 1)} \
                                    | {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9'} \
                                    | {'_', '.', '-', '+', '#'}

    def __new__(cls, content):
        for char in content:
            if char not in cls.allowed_identifiers:
                raise ValueError(f"Failed to create Identifier({content}): Character '{char}' is not allowed.\n"
                                 f"Use one of {list(sorted(cls.allowed_identifiers))}")
        # noinspection PyArgumentList
        return str.__new__(cls, content)


@dataclass(frozen=True)
class ScoreboardValue:
    value: Identifier
    scoreboard: Scoreboard

    def __str__(self):
        return f"{self.value} {self.scoreboard.get_name()}"


@dataclass(frozen=True)
class DataPath:
    storage: ResourceSpecifier
    path: List[str]

    def dotted_path(self) -> str:
        return ".".join(self.path)

    def get_last(self) -> str:
        return self.path[-1]

    def last_element_indexed(self, index: int) -> DataPath:
        new_path = self.path[:]
        new_path[-1] += f"[{index}]"
        return DataPath(self.storage, new_path)

    def __add__(self, other: str) -> DataPath:
        if not isinstance(other, str):
            return NotImplemented

        new_path = self.path[:]
        new_path.append(other)
        return DataPath(self.storage, new_path)

from dataclasses import dataclass, field
from typing import List, Tuple

from lark import Token, Tree


@dataclass()
class VariableAccess:
    access: Tree
    master_context: Tuple[int, int]


@dataclass()
class VariableContext:
    identifier: Token
    # a tuple (line, column) identifying the master context
    declaration: VariableAccess
    static_declaration: bool
    member_declaration: bool
    reads: List[VariableAccess] = field(default_factory=list)
    writes: List[VariableAccess] = field(default_factory=list)

    def history(self) -> List[Tuple[str, VariableAccess]]:
        accesses = [("read", i) for i in self.reads]
        accesses.extend(("write", i) for i in self.writes)

        accesses.sort(key=lambda x: x[1].access.line)

        return accesses

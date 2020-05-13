from dataclasses import dataclass, field
from typing import List

from lark import Token, Tree


@dataclass()
class VariableAccess:
    access: Tree
    contextId: int


@dataclass()
class VariableContext:
    identifier: Token
    declaration: VariableAccess
    static_declaration: bool
    member_declaration: bool
    reads: List[VariableAccess] = field(default_factory=list)
    writes: List[VariableAccess] = field(default_factory=list)

    def history(self):
        accesses = [("read", i) for i in self.reads]
        accesses.extend(("write", i) for i in self.writes)

        accesses.sort(key=lambda x: x[1].access.line)

        return accesses

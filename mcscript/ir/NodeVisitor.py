from __future__ import annotations

from typing import Dict, Iterator, Set

from mcscript.ir import IRNode
from mcscript.ir.components import FunctionNode, FunctionCallNode


class NodeVisitor:
    def __init__(self, node: FunctionNode, nodes: Dict[str, FunctionNode]):
        self.node = node
        self.nodes = nodes

        self._pending_remove: Set[IRNode] = set()

    def mark_remove(self, node: IRNode):
        self._pending_remove.add(node)

    def visit_all(self) -> Iterator[IRNode]:
        yield from self._visit_all(self.node, set())

        if self._pending_remove:
            raise ValueError(f"Could not delete nodes: {self._pending_remove}")

    def _visit_all(self, node: IRNode, called_functions: Set[IRNode]) -> Iterator[IRNode]:
        for child in node.inner_nodes:
            if isinstance(child, FunctionCallNode):
                if child in called_functions:
                    raise RecursionError("Recursion is not yet supported!")
                called_functions.add(child)
                yield from self._visit_all(self.nodes[child["name"].path], called_functions)
            else:
                yield child

                yield from self._visit_all(child, called_functions)

        pending_remove = set()
        for to_remove in self._pending_remove:
            if to_remove in node.inner_nodes:
                node.inner_nodes.remove(to_remove)
            else:
                pending_remove.add(to_remove)
        self._pending_remove = pending_remove

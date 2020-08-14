from __future__ import annotations

from typing import Dict, Iterator, Set

from mcscript.ir import IRNode
from mcscript.ir.components import FunctionNode


class NodeVisitor:
    def __init__(self, node: FunctionNode, nodes: Dict[str, FunctionNode]):
        self.node = node
        self.nodes = nodes

        self._pending_remove: Set[IRNode] = set()

    def mark_remove(self, node: IRNode):
        self._pending_remove.add(node)

    def visit_top_functions(self) -> Iterator[FunctionNode]:
        """
        Visits all top-level functions
        """
        return iter(self.nodes.values())

    def visit_node(self, node: IRNode) -> Iterator[IRNode]:
        return iter(node.inner_nodes)

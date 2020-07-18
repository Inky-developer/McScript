from contextlib import contextmanager
from typing import List, Union, Generator, Iterable

from mcscript.ir import IRNode
from mcscript.ir.components import FunctionNode
from mcscript.utils.resources import Identifier


class IrMaster:
    """
    Interface for construction of ir-nodes
    """

    def __init__(self):
        # A list of all defined functions
        self.function_nodes: List[FunctionNode] = []

        # A list of list of nodes. Popped after the end of `with_function` and added to function_nodes as a function.
        self.active_nodes: List[List[IRNode]] = []

    def append(self, node: IRNode):
        self.active_nodes[-1].append(node)

    def append_all(self, first: Union[IRNode, Iterable[IRNode]], *nodes: IRNode):
        if isinstance(first, Iterable):
            if nodes:
                raise ValueError("Cannot accept both iterable and varargs")
            nodes = first

        for node in nodes:
            self.append(node)

    @contextmanager
    def with_function(self, name: str):
        """ Useful for procedurally generating a function file """

        self.active_nodes.append([])

        try:
            yield
        finally:
            self.function_nodes.append(FunctionNode(Identifier(name), self.active_nodes.pop()))

    @contextmanager
    def with_buffer(self) -> Generator[List[IRNode], None, None]:
        """ Buffers all nodes and yields their holding list"""
        buffer = []
        self.active_nodes.append(buffer)

        try:
            yield buffer
        finally:
            self.active_nodes.pop()

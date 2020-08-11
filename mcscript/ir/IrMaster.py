from __future__ import annotations

from contextlib import contextmanager
from typing import List, Union, Generator, Iterable, Optional

from mcscript.ir import IRNode
from mcscript.ir.components import FunctionNode
from mcscript.ir.optimize import optimize
from mcscript.utils.resources import Identifier, SourceLocation, ResourceSpecifier


class IrMaster:
    """
    Interface for construction of ir-nodes
    """

    def __init__(self):
        # A list of all defined functions
        self.function_nodes: List[FunctionNode] = []

        # A list of list of nodes. Popped after the end of `with_function` and added to function_nodes as a function.
        self.active_nodes: List[List[IRNode]] = []

        self.node_counter = 0
        self._source_location: SourceLocation = None  # set by compile state
    
    def optimize(self):
        """ Optimizes the contained function nodes"""
        # expensive optimization pass
        # ToDo: real Debug mode
        DEBUG = False
        if not DEBUG:
            (start_node,) = [i for i in self.function_nodes if i["name"] == "main"]
            optimize(start_node, self.function_nodes)

        # simple optimization pass
        function_nodes = [i.optimized(self, None)[0] for i in self.function_nodes]
        self.function_nodes = [i for i in function_nodes if not i["drop"]]

    def append(self, node: IRNode):
        self.active_nodes[-1].append(node)

        # Done after the function node is created
        # self._incr_index(node)

    def append_all(self, first: Union[IRNode, Iterable[IRNode]], *nodes: IRNode):
        if isinstance(first, Iterable):
            if nodes:
                raise ValueError("Cannot accept both iterable and varargs")
            nodes = first

        for node in nodes:
            self.append(node)

    def find_function_node(self, name: ResourceSpecifier) -> Optional[FunctionNode]:
        return next((i for i in self.function_nodes if i["name"] == name.path), None)

    def set_current_source_location(self, source_location: SourceLocation):
        self._source_location = source_location

    @contextmanager
    def with_function(self, name: str):
        """ Useful for procedurally generating a function file """

        self.active_nodes.append([])

        try:
            yield
        finally:
            node = FunctionNode(
                Identifier(name), self.active_nodes.pop()
            )
            self._incr_index(node)
            self.function_nodes.append(node)

    @contextmanager
    def with_buffer(self, buffer=None) -> Generator[List[IRNode], None, None]:
        """ Buffers all nodes and yields their holding list"""
        buffer = [] if buffer is None else buffer
        self.active_nodes.append(buffer)

        try:
            yield buffer
        finally:
            self.active_nodes.pop()

    @contextmanager
    def with_previous(self):
        """ 
        adds a reference to the previous node to the top of the stack
        so that temporary writes to the parent node list are possible.
        Fails if no previous stack exists.
        """
        with self.with_buffer(self.active_nodes[-2]) as buffer:
            yield buffer

    def _incr_index(self, node: IRNode):
        node.metadata.index = self.node_counter
        self.node_counter += 1

        for child in node.inner_nodes:
            self._incr_index(child)

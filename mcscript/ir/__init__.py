"""
Intermediate representation module.
Provides dataclasses as instructions which have a one-to-one translation for minecraft code.
Great potential for optimization.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Tuple, Iterator, TypeVar, Type, Union

from mcscript.utils.resources import SourceLocation
from mcscript.utils.utils import camel_case_to_snake_case

if TYPE_CHECKING:
    from mcscript.ir.IrMaster import IrMaster


@dataclass()
class IrNodeMetadata:
    # line and column which cause this node to generate
    source_location: Optional[SourceLocation] = field(default=None)

    index: Optional[int] = field(default=None)


T = TypeVar("T")


class IRNode:
    """ Base node for the intermediate representation."""

    def __init__(self, inner_nodes: List[IRNode] = None, metadata: Optional[IrNodeMetadata] = None):
        self.inner_nodes: List[IRNode] = inner_nodes or []

        # A list of all data that store IrNodes so all contained nodes can be looked up
        # A str is interpreted as key of self.data
        self.lookup_nodes: List[str] = []

        # A dictionary used to store other important data about this node
        self.data: Dict[str, Any] = {}

        # metadata which can be used for debug information or optimizations
        self.metadata: IrNodeMetadata = metadata or IrNodeMetadata()

        # A list of nodes that should be discarded
        self.discarded_inner_nodes: List[IRNode] = []

    def allow_inline_optimization(self) -> bool:
        """
        Returns:
            whether this node can be safely inlined
        """
        return len(self.inner_nodes) <= 1

    def optimized(self, ir_master: IrMaster, parent: Optional[IRNode]) -> \
            Tuple[Union[IRNode, Tuple[IRNode, ...]], bool]:
        """
        Optimizes this node.
        If no optimizations can be made, the same node should be returned.

        Args:
            ir_master: the ir master object
            parent: all neighbouring nodes of this node (same level)

        Returns:
            The new IrNode and whether an optimization could be made
        """
        changed = False
        index = 0
        while index < len(self.inner_nodes):
            node = self.inner_nodes[index]
            optimized_node, has_changed = node.optimized(ir_master, self)
            if has_changed:
                if isinstance(optimized_node, IRNode):
                    self.inner_nodes[index] = optimized_node
                else:
                    # insert the list of new nodes
                    self.inner_nodes = self.inner_nodes[:index] + list(optimized_node) + self.inner_nodes[index + 1:]
                changed = True
            else:
                index += 1

            if self.clear_discarded_nodes():
                index -= 1

        return self, changed

    def clear_discarded_nodes(self) -> bool:
        ret = len(self.discarded_inner_nodes) != 0
        for node in self.discarded_inner_nodes:
            node_index = self.inner_nodes.index(node)
            del self.inner_nodes[node_index]
        self.discarded_inner_nodes.clear()
        return ret

    def iter_nested_nodes(self) -> Iterator[IRNode]:
        """
        Iterates over all contained nodes
        """
        for node in self.lookup_nodes:
            node_thing = self[node]
            if isinstance(node_thing, IRNode):
                yield node_thing
            elif isinstance(node_thing, list):
                for i in node_thing:
                    if not isinstance(i, IRNode):
                        raise ValueError
                    yield i
            else:
                raise ValueError

    def iter_nested_nodes_recursively(self) -> Iterator[IRNode]:
        for node in self.iter_nested_nodes():
            yield node
            yield from node.iter_nested_nodes_recursively()

    def iter_data_of_type(self, the_type: Type[T]) -> Iterator[Tuple[IRNode, str, T]]:
        """
        Goes through all data that this node stores and yields it if it has the specified type
        Recursively checks all nested nodes.

        Args:
            the_type: The type to look for

        Returns:
            An iterator over the node that has data of this type, the accessor name and the data itself
        """
        for key, value in self.data.items():
            if isinstance(value, the_type):
                yield self, key, value

        for node in self.iter_nested_nodes():
            yield from node.iter_data_of_type(the_type)

    @cached_property
    def node_id(self) -> str:
        return camel_case_to_snake_case(type(self).__name__)

    def as_tree(self, level=1) -> str:
        spacer = "  " * level
        children = f"\n{spacer}|-".join(child.as_tree(level + 1) for child in self.inner_nodes)

        # get all other set attrs
        attributes = []
        for attribute in self.data:
            value = self.data[attribute]
            if isinstance(value, list):
                value = "[" + ", ".join(str(i) for i in value) + "]"
            attributes.append((attribute, value))
        attributes = ", ".join(
            f"{k}={v}" for k, v in attributes)

        metadata = []
        for key in vars(self.metadata):
            value = getattr(self.metadata, key)
            if value is not None:
                metadata.append((key, value))
        metadata = ", ".join(f"{key}: \"{repr(value)}\"" for key, value in metadata)

        return f"{self.__class__.__name__}({attributes})" \
               + (" # " + metadata if metadata else "") \
               + (f"\n{spacer}|-{children}" if children else "")

    def __str__(self):
        return self.as_tree()

    def __setitem__(self, key, value):
        self.data[key] = value

        # make sure every stored IrNode is added to lookup_nodes
        if isinstance(value, IRNode):
            self.lookup_nodes.append(key)
        elif isinstance(value, list):
            if any(isinstance(i, IRNode) for i in value):
                self.lookup_nodes.append(key)

    def __getitem__(self, item):
        return self.data[item]

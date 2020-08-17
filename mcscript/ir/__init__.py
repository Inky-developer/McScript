"""
Intermediate representation module.
Provides dataclasses as instructions which have a one-to-one translation for minecraft code.
Great potential for optimization.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import List, Dict, Any, Optional, TYPE_CHECKING, Tuple, TypeVar, Union

from mcscript.utils.resources import ScoreboardValue
from mcscript.utils.utils import camel_case_to_snake_case

if TYPE_CHECKING:
    from mcscript.ir.IrMaster import IrMaster


@dataclass()
class IrNodeMetadata:
    index: Optional[int] = field(default=None)


T = TypeVar("T")


class IRNode:
    """ Base node for the intermediate representation."""

    def __init__(self, inner_nodes: List[IRNode] = None, metadata: Optional[IrNodeMetadata] = None):
        self.inner_nodes: List[IRNode] = inner_nodes or []

        # A dictionary used to store other important data about this node
        self.data: Dict[str, Any] = {}

        # metadata which can be used for debug information or optimizations
        self.metadata: IrNodeMetadata = metadata or IrNodeMetadata()

        # A list of nodes that should be discarded
        self.discarded_inner_nodes: List[IRNode] = []

    def reads_scoreboard_value(self, scoreboard_value: ScoreboardValue) -> bool:
        """
        Returns whether this node or any inner node reads this score

        Args:
            scoreboard_value: The scoreboard value
        """
        return scoreboard_value in self.read_scoreboard_values() or any(
            i.reads_scoreboard_value(scoreboard_value) for i in self.inner_nodes
        )

    def writes_scoreboard_value(self, scoreboard_value: ScoreboardValue) -> bool:
        """
        Returns whether this node or any inner node writes to this score

        Args:
            scoreboard_value: The scoreboard value
        """
        return scoreboard_value in self.written_scoreboard_values() or any(
            i.writes_scoreboard_value(scoreboard_value) for i in self.inner_nodes
        )

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
                index = 0

        return self, changed

    def clear_discarded_nodes(self) -> bool:
        ret = len(self.discarded_inner_nodes) != 0
        for node in self.discarded_inner_nodes:
            node_index = self.inner_nodes.index(node)
            del self.inner_nodes[node_index]
        self.discarded_inner_nodes.clear()
        return ret

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
            attributes.append((attribute, self._format_data(attribute, value)))
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

    def read_scoreboard_values(self) -> List[ScoreboardValue]:
        """
        Returns all scoreboard values that this node reads
        """
        return []

    def written_scoreboard_values(self) -> List[ScoreboardValue]:
        """
        Returns all scoreboard values that this node writes to
        """
        return []

    def _format_data(self, key: str, value: Any) -> str:
        return str(value)

    def __str__(self):
        return self.as_tree()

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, item):
        return self.data[item]

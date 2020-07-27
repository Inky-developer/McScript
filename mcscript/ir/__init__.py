"""
Intermediate representation module.
Provides dataclasses as instructions which have a one-to-one translation for minecraft code.
Great potential for optimization.
"""
from __future__ import annotations

from functools import cached_property
from typing import List, Dict, Any, Optional, Type, TYPE_CHECKING, Tuple
from dataclasses import dataclass, field

from mcscript.utils.utils import camel_case_to_snake_case
from mcscript.utils.resources import SourceLocation

if TYPE_CHECKING:
    from mcscript.ir.IrMaster import IrMaster

@dataclass()
class IrNodeMetadata:
    # line and column which cause this node to generate
    source_location: Optional[SourceLocation] = field(default=None)

    index: Optional[int] = field(default=None)
    

class IRNode:
    """ Base node for the intermediate representation."""

    def __init__(self, inner_nodes: List[IRNode] = None, metadata: Optional[IrNodeMetadata] = None):
        self.inner_nodes = inner_nodes or []

        # A dictionary used to store other important data about this node
        self.data: Dict[str, Any] = {}

        # metadata which can be used for debug information or optimizations
        self.metadata: IrNodeMetadata = metadata or IrNodeMetadata()
    
    def optimized(self, ir_master: IrMaster) -> Tuple[IRNode, bool]:
        """
        Optimizing the node tree logically.
        If not optimizations can be made, return self.
        """
        changed = False
        index = 0
        while index < len(self.inner_nodes):
            node = self.inner_nodes[index]
            optimized_node, has_changed = node.optimized(ir_master)
            if has_changed:
                self.inner_nodes[index] = optimized_node
                changed = True
            else:
                index += 1
        
        return self, changed
    
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

    def __getitem__(self, item):
        return self.data[item]

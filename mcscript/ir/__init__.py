"""
Intermediate representation module.
Provides dataclasses as instructions which have a one-to-one translation for minecraft code.
Great potential for optimization.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass()
class IrNodeMetadata:
    # line and column which cause this node to generate
    line: Optional[int] = field(default=None)
    column: Optional[int] = field(default=None)
    

class IRNode:
    """ Base node for the intermediate representation."""

    def __init__(self, inner_nodes: List[IRNode] = None, metadata: Optional[IrNodeMetadata] = None):
        self.inner_nodes = inner_nodes or []

        # A dictionary used to store other important data about this node
        self.data: Dict[str, Any] = {}

        # metadata which can be used for debug information or optimizations
        self.metadata: IrNodeMetadata = metadata or IrNodeMetadata()

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

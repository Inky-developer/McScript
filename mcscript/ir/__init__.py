"""
Intermediate representation module.
Provides dataclasses as instructions which have a one-to-one translation for minecraft code.
Great potential for optimization.
"""
from __future__ import annotations

from typing import List, Dict, Any


class IRNode:
    """ Base node for the intermediate representation."""

    def __init__(self, inner_nodes: List[IRNode] = None, **metadata):
        self.inner_nodes = inner_nodes or []

        # A dictionary used to store other important data about this node
        self.data: Dict[str, Any] = {}

        # metadata which can be used for debug information or optimizations
        self.metadata: Dict[str, any] = metadata or {}

    def as_tree(self, level=1) -> str:
        spacer = "  " * level
        children = f"\n{spacer}|-".join(child.as_tree(level + 1) for child in self.inner_nodes)

        # get all other set attrs
        attributes = ", ".join(
            f"{i}={str(self.data[i])}" for i in self.data)

        metadata = ",".join(f"{key}: \"{self.metadata[key]}\"" for key in self.metadata)

        return f"{self.__class__.__name__}({attributes})" \
               + (" # " + metadata if self.metadata else "") \
               + (f"\n{spacer}|-{children}" if children else "")

    def __str__(self):
        return self.as_tree()

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, item):
        return self.data[item]

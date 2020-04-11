from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from mcscript.data.minecraftData.blocks import Block


@dataclass
class BlockTree:
    values: List[Block]
    left: Optional[BlockTree]
    right: Optional[BlockTree]
    index: int
    reverse_index: int

    def walk(self):
        yield self.left, self.right, self
        if self.left:
            yield from self.left.walk()
        if self.right:
            yield from self.right.walk()

    @staticmethod
    def fromList(blocks: List[Block], index=0) -> BlockTree:
        """
        splits the list recursively and creates a BlockTree from it.
        :param index: the index
        :param blocks: A list of the blocks
        :return: a BlockTree object
        """

        left = blocks[:int(len(blocks) / 2 + 0.5)]
        right = blocks[len(left):]

        treeLeft = treeRight = None
        oldIndex = index

        if len(left) > 1:
            treeLeft = BlockTree.fromList(left, index + 1)
            index = treeLeft.index + 1
        if len(right) > 1:
            treeRight = BlockTree.fromList(right, index + 1)
            index = treeRight.index + 1

        return BlockTree(blocks, treeLeft, treeRight, index, oldIndex)

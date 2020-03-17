from typing import List

from src.mcscript.data.blockStorage.BlockTree import BlockTree
from src.mcscript.data.minecraftData.blocks import Blocks, Block


class BlockStorage:
    # ToDo: add support for blockstates
    def __init__(self):
        self.blocks: List[Block] = Blocks.getBlocks()

    def createTree(self) -> BlockTree:
        return BlockTree.fromList(self.blocks)


if __name__ == '__main__':
    tree = BlockStorage().createTree()

from __future__ import annotations

import re
from dataclasses import dataclass, field
from itertools import product
from typing import List, Generator, Optional

from mcscript.data import getBlocks


@dataclass(frozen=True)
class BlockstateValue:
    blockstate: Blockstate = field(repr=False)
    value: str


@dataclass(frozen=True)
class Blockstate:
    id: str
    values: List[str] = field(default_factory=list)

    def getValues(self) -> List[BlockstateValue]:
        return [BlockstateValue(self, value) for value in self.values]

    @staticmethod
    def getBlockstateString(*blockstates: BlockstateValue):
        if not blockstates:
            return ""
        return "[" + ",".join(f"{value.blockstate.id}={value.value}" for value in blockstates) + "]"


@dataclass(frozen=True)
class BlockstateBlock:
    block: Block
    state: List[BlockstateValue]

    def getMinecraftName(self):
        return self.block.minecraft_id + Blockstate.getBlockstateString(*self.state)


@dataclass(frozen=True)
class Block:
    minecraft_id: str
    name: str
    index: int
    blockstates: List[Blockstate] = field(default_factory=list)

    def getNumberBlockstates(self):
        result = 1
        for blockstate in self.blockstates:
            result *= len(blockstate.values)
        return result

    def getBlockstatePermutations(self) -> Generator[List[BlockstateValue]]:
        yield from product(*(blockstate.getValues() for blockstate in self.blockstates))

    def getBlockstate(self, identifier: str) -> Blockstate:
        for blockstate in self.blockstates:
            if blockstate.id == identifier:
                return blockstate
        b = Blockstate(identifier)
        self.blockstates.append(b)
        return b


class _Blocks:
    """
    This class keeps track of all blocks that are currently in the game
    """
    PATTERN_BLOCKSTATES = re.compile(r"(?:(\w+)=(\w+))+")

    def __init__(self):
        self.loaded = False
        self.blocks: List[Block] = []

    def assertLoaded(self):
        if not self.loaded:
            self.reload()
            self.loaded = True

    def reload(self):
        self.blocks = []

        currentBlock = None
        for index, blockName in enumerate(getBlocks().split("\n")):
            if not blockName:
                continue
            minecraft_id = blockName.split("[")[0]
            block = Block(minecraft_id, minecraft_id.split(":")[-1], index)

            if not currentBlock or currentBlock.minecraft_id != block.minecraft_id:
                currentBlock = block
                self.blocks.append(block)

            blockstates = self.PATTERN_BLOCKSTATES.findall(blockName.split("[")[-1])
            for blockstate in blockstates:
                identifier, value = (i.lower() for i in blockstate)
                values = currentBlock.getBlockstate(identifier).values
                if value not in values:
                    values.append(value)

    def getBlock(self, index: int) -> Block:
        self.assertLoaded()
        return self.blocks[index]

    def getBlockstateIndexed(self, index: int) -> Optional[BlockstateBlock]:
        lastBlock = None
        for block in self.getBlocks():
            if block.index > index:
                break
            lastBlock = block

        if lastBlock.index == index and not lastBlock.blockstates:
            return BlockstateBlock(lastBlock, [])
        for blockstateId, blockstate in enumerate(lastBlock.getBlockstatePermutations()):
            if lastBlock.index + blockstateId == index:
                return BlockstateBlock(lastBlock, blockstate)
        return None

    def findBlockByName(self, name: str) -> Optional[Block]:
        for block in self.getBlocks():
            if block.name == name:
                return block
        return None

    def getBlocks(self) -> List[Block]:
        self.assertLoaded()
        return self.blocks


Blocks = _Blocks()


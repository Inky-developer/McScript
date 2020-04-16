from __future__ import annotations

from dataclasses import dataclass, field
from itertools import product
from typing import Generator, List, Optional

from mcscript.assets import getCurrentData


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


BLOCKS = []


def assertLoaded():
    if not BLOCKS:
        blockJson = getCurrentData().getData("blocks")
        for blockId in blockJson:
            properties = blockJson[blockId].get("properties", [])
            blockstates = [Blockstate(i, properties[i]) for i in properties]

            blockIndex = float("inf")
            permutations = blockJson[blockId]["states"]
            for permutation in permutations:
                blockIndex = min(blockIndex, permutation["id"])

            BLOCKS.append(Block(blockId, blockId.split("minecraft:")[1], blockIndex, blockstates))


def getBlocks() -> List[Block]:
    assertLoaded()
    return BLOCKS


def getBlock(index: int) -> Block:
    assertLoaded()
    return BLOCKS[index]


def getBlockstateIndexed(index: int) -> Optional[BlockstateBlock]:
    assertLoaded()

    lastBlock: Optional[Block] = None
    for block in BLOCKS:
        if block.index > index:
            break
        lastBlock = block

    if lastBlock is None:
        raise ValueError(f"Unknown blockstate {index}")

    if lastBlock.index == index and not lastBlock.blockstates:
        return BlockstateBlock(lastBlock, [])

    for blockstateId, blockstate in enumerate(lastBlock.getBlockstatePermutations()):
        if lastBlock.index + blockstateId == index:
            return BlockstateBlock(lastBlock, blockstate)

# def getBlock(self, index: int) -> Block:
#     self.assertLoaded()
#     return self.blocks[index]
#
# def getBlockstateIndexed(self, index: int) -> Optional[BlockstateBlock]:
#     lastBlock = None
#     for block in self.getBlocks():
#         if block.index > index:
#             break
#         lastBlock = block
#
#     if lastBlock.index == index and not lastBlock.blockstates:
#         return BlockstateBlock(lastBlock, [])
#     for blockstateId, blockstate in enumerate(lastBlock.getBlockstatePermutations()):
#         if lastBlock.index + blockstateId == index:
#             return BlockstateBlock(lastBlock, blockstate)
#     return None

from abc import ABC, abstractmethod
from typing import List

from mcscript.data import getDictionaryResource
from mcscript.data.blockStorage import BlockTree
from mcscript.data.commands import Command, Config, ExecuteCommand, multiple_commands
from mcscript.data.minecraftData.blocks import Block, Blocks, Blockstate, BlockstateValue
from mcscript.utils.FileStructure import FileStructure


def resetToZero():
    return Command.SET_VALUE(
        stack=Config.currentConfig.RETURN_SCORE,
        value=-1
    ) + "\n"


class Generator(ABC):
    def __init__(self, tree: BlockTree):
        self.tree = tree

    @abstractmethod
    def generate(self, filestructure: FileStructure, *data):
        pass


class BlockTagGenerator(Generator):
    def generate(self, filestructure: FileStructure, *_):
        name = "block.{}.json"
        fmt_string = getDictionaryResource("DefaultFiles.txt")["tag_block"]

        iterator = iter(self.tree.walk())
        next(iterator)  # skip first element, no tag with all blocks necessary

        for _, _, tree in iterator:
            filestructure.pushFile(name.format(tree.index))
            filestructure.get().write(fmt_string.format(self.format_blocks(tree.values)))

    @staticmethod
    def format_blocks(blocks: List[Block]):
        return ",\n        ".join(f'"{block.minecraft_id}"' for block in blocks)


class BlockStateGenerator(ABC):
    def __init__(self, block: Block):
        self.block = block

    @abstractmethod
    def generate(self, filestructure: FileStructure):
        pass


class BlockStateFunctionGenerator(BlockStateGenerator):
    """
    Tests for all blockstates of a block. Currently o(n) performance.
    """

    def generate(self, filestructure: FileStructure):
        for index, perm in enumerate(self.block.getBlockstatePermutations()):
            filestructure.get().write(self.checkBlock(perm, index))

    def checkBlock(self, perm: List[BlockstateValue], permIndex: int):
        return Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=Config.currentConfig.RETURN_SCORE,
                range=-1,
                command=ExecuteCommand.IF_BLOCK(block=self.block.minecraft_id + Blockstate.getBlockstateString(*perm))
            ),
            command=Command.SET_VALUE(
                stack=Config.currentConfig.RETURN_SCORE,
                value=self.block.index + permIndex
            )
        ) + "\n"


class BlockFunctionGenerator(Generator):
    def generate(self, filestructure: FileStructure, *_):
        name = "get_block.{}"

        # filestructure.pushFile(name.format(0))
        # filestructure.get().write(self.resetToZero())
        isFirst = True
        for left, right, tree in self.tree.walk():
            filestructure.pushFile(name.format(tree.reverse_index))
            if isFirst:
                isFirst = False
                filestructure.get().write(resetToZero())
            if not left:
                if len(tree.values) != 2:
                    raise Exception("You should never see this")
                for block in tree.values:
                    BlockStateFunctionGenerator(block).generate(filestructure)
            else:
                filestructure.get().writelines(
                    self.checkBlockTag(tree.left.index, name.format(tree.left.reverse_index)))
                if not right:
                    BlockStateFunctionGenerator(tree.values[-1]).generate(filestructure)
                else:
                    filestructure.get().writelines(
                        self.checkBlockTag(tree.right.index, name.format(tree.right.reverse_index)))

    @staticmethod
    def checkBlockTag(index: int, function: str):
        return Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=Config.currentConfig.RETURN_SCORE,
                range=-1,
                command=ExecuteCommand.IF_BLOCK(block=f"#{Config.currentConfig.UTILS}:block.{index}")
            ),
            command=Command.RUN_FUNCTION(
                name=Config.currentConfig.UTILS,
                function=function
            )
        ) + "\n"


class IdToBlockGenerator:
    FUNCTION_NAME_TEMPLATE = "set_block.{}"

    def generate(self, filestructure: FileStructure, *data):
        var1, var2 = data
        tempBlock = Blocks.getBlock(-1)
        lastIndex = tempBlock.index + tempBlock.getNumberBlockstates()

        self.generateRecursive(var1, var2, filestructure, lastIndex)

    def generateRecursive(self, var1, var2, filestructure, count, start=0, index=0):
        filestructure.pushFile(self.FUNCTION_NAME_TEMPLATE.format(index))
        file = filestructure.get()
        if index == 0:
            file.write(resetToZero())
        pivotIndex = int(count / 2 + 0.5)
        left = pivotIndex
        right = count - pivotIndex
        if left > 1:
            file.write(self.checkRangeLess(var1, var2, start + left, self.FUNCTION_NAME_TEMPLATE.format(index + 1)))
            index = self.generateRecursive(var1, var2, filestructure, left, start, index + 1)
        else:
            file.write(self.checkBlock(var1, var2, left + start - 1))
        if right > 1:
            file.write(
                self.checkRangeMoreOrEqual(var1, var2, left + start, self.FUNCTION_NAME_TEMPLATE.format(index + 1)))
            index = self.generateRecursive(var1, var2, filestructure, right, left + start, index + 1)
        else:
            file.write(self.checkBlock(var1, var2, right + left + start - 1))
        filestructure.popFile()
        return index

    def checkRangeLess(self, a, b, value, function):
        return self.checkRange(a, b, f"..{value - 1}", function)

    def checkRangeMoreOrEqual(self, a, b, value, function):
        return self.checkRange(a, b, f"{value}..", function)

    def checkRange(self, a, b, range_, function):
        return Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=a,
                range=-1,
                command=ExecuteCommand.IF_SCORE_RANGE(
                    stack=b,
                    range=range_
                )
            ),
            command=Command.RUN_FUNCTION(
                name=Config.currentConfig.UTILS,
                function=function
            )
        ) + "\n"

    def checkBlock(self, a, b, value):
        block = Blocks.getBlockstateIndexed(value)
        checkScores = Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=a,
                range=-1,
                command=ExecuteCommand.IF_SCORE_RANGE(
                    stack=b,
                    range=value
                )
            ),
            command="{}"
        )
        return multiple_commands(
            checkScores.format(Command.SET_BLOCK(block=block.getMinecraftName())),
            checkScores.format(Command.SET_VALUE(
                stack=a,
                value=1
            )) + "\n"
        )

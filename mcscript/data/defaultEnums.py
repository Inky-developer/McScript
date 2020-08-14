from typing import Optional

from mcscript.data.minecraftData import blocks
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.IntegerResource import IntegerResource


def makeBlocks() -> EnumResource:
    names = {block.name: IntegerResource(block.index, None) for block in blocks.getBlocks()}
    return EnumResource(**names)


ENUMS = {
    "blocks": makeBlocks,
}


def get(value: str) -> Optional[EnumResource]:
    function = ENUMS.get(value, None)
    if function is None:
        return None
    return function()

from typing import Optional

from src.mcscript.data.blocks import Blocks
from src.mcscript.lang.Resource.EnumResource import EnumResource
from src.mcscript.lang.Resource.NumberResource import NumberResource


def makeBlocks() -> EnumResource:
    names = {block.name: NumberResource(block.index, True) for block in Blocks.getBlocks()}
    return EnumResource(**names)


ENUMS = {
    "blocks": makeBlocks,
}


def get(value: str) -> Optional[EnumResource]:
    function = ENUMS.get(value, None)
    if function is None:
        return None
    return function()

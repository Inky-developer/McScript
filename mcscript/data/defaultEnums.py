from typing import Optional

from mcscript.data.Config import Config
from mcscript.data.minecraftData import blocks
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.IntegerResource import IntegerResource


def makeBlocks(config: Config) -> EnumResource:
    names = {block.name: IntegerResource(block.index, None) for block in blocks.getBlocks(config)}
    return EnumResource(**names)


ENUMS = {
    "blocks": makeBlocks,
}


def get(value: str, config: Config) -> Optional[EnumResource]:
    function = ENUMS.get(value, None)
    if function is None:
        return None
    return function(config)

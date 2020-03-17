from typing import Optional

from src.mcscript.data.minecraftData import biomes, features
from src.mcscript.data.minecraftData.blocks import Blocks
from src.mcscript.lang.Resource.EnumResource import EnumResource
from src.mcscript.lang.Resource.NumberResource import NumberResource


def makeBlocks() -> EnumResource:
    names = {block.name: NumberResource(block.index, True) for block in Blocks.getBlocks()}
    return EnumResource(**names)


def makeBiomes() -> EnumResource:
    names = {biome.name: NumberResource(biome.protocol_id, True) for biome in biomes.getBiomes()}
    return EnumResource(**names)


def makeFeatures() -> EnumResource:
    names = {feature.name: NumberResource(feature.protocol_id, True) for feature in features.getFeatures()}
    return EnumResource(**names)


ENUMS = {
    "blocks": makeBlocks,
    "biomes": makeBiomes,
    "features": makeFeatures
}


def get(value: str) -> Optional[EnumResource]:
    function = ENUMS.get(value, None)
    if function is None:
        return None
    return function()

from typing import Optional

from mcscript.data.minecraftData import biomes, blocks, features
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.IntegerResource import IntegerResource


def makeBlocks() -> EnumResource:
    names = {block.name: IntegerResource(block.index, None) for block in blocks.getBlocks()}
    return EnumResource(**names)


def makeBiomes() -> EnumResource:
    names = {biome.name: IntegerResource(biome.protocol_id, None) for biome in biomes.getBiomes()}
    return EnumResource(**names)


def makeFeatures() -> EnumResource:
    names = {feature.name: IntegerResource(feature.protocol_id, None) for feature in features.getFeatures()}
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

from typing import Optional

from mcscript.data.minecraftData import biomes, blocks, features
from mcscript.lang.resource.EnumResource import EnumResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceType import ResourceType


def makeBlocks() -> EnumResource:
    names = {block.name: NumberResource(block.index, True) for block in blocks.getBlocks()}
    return EnumResource(**names)


def makeBiomes() -> EnumResource:
    names = {biome.name: NumberResource(biome.protocol_id, True) for biome in biomes.getBiomes()}
    return EnumResource(**names)


def makeFeatures() -> EnumResource:
    names = {feature.name: NumberResource(feature.protocol_id, True) for feature in features.getFeatures()}
    return EnumResource(**names)


def makeTypes() -> EnumResource:
    """ enum which has all named resource types as members"""
    names = {i.value: i for i in ResourceType if not isinstance(i.value, int)}
    return EnumResource(**names)


ENUMS = {
    "blocks": makeBlocks,
    "biomes": makeBiomes,
    "features": makeFeatures,
    "types": makeTypes,
}


def get(value: str) -> Optional[EnumResource]:
    function = ENUMS.get(value, None)
    if function is None:
        return None
    return function()

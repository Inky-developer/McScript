import json
from dataclasses import dataclass
from typing import List

from mcscript.data import getBiomes as getBiomesRaw


@dataclass(frozen=True)
class Biome:
    id: str
    # protocol id makes jumps
    protocol_id: int
    index: int

    @property
    def name(self):
        return self.id.split(":")[-1]


BIOMES: List[Biome] = []
loaded = False


def assertLoaded():
    global BIOMES, loaded
    if not loaded:
        biomeJson = getBiomesRaw()
        biomeDict = json.loads(biomeJson)
        for index, key in enumerate(biomeDict):
            BIOMES.append(Biome(key, biomeDict[key]["protocol_id"], index))
        loaded = True


def getBiomes() -> List[Biome]:
    assertLoaded()
    return BIOMES

from __future__ import annotations

from typing import Tuple

from mcscript.data import getDictionaryResource
from mcscript.data.minecraftData import biomes
from mcscript.data.predicates.predicateGenerator import PredicateGenerator


class BiomePredicate(PredicateGenerator):
    """
    generates predicates to identify each biome in minecraft (biomes are read from config/biome_list_path)
    """

    def generate(self, fileStructure: FileStructure) -> Tuple[str, ...]:
        predicate = getDictionaryResource("DefaultFiles.txt")["predicate_biome"]
        predicates = []
        for biome in biomes.getBiomes():
            name = f"predicate_biome_{biome.name}"
            predicates.append(name)
            fileStructure.pushFile(name + ".json")
            fileStructure.get().write(stringFormat(predicate, biome=biome.id))
            fileStructure.popFile()

        return tuple(predicates)

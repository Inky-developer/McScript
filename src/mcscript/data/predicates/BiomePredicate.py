from typing import Tuple

from src.mcscript.data import getDictionaryResource
from src.mcscript.data.Commands import stringFormat
from src.mcscript.data.minecraftData import biomes
from src.mcscript.data.predicates.PredicateGenerator import PredicateGenerator
from src.mcscript.utils.FileStructure import FileStructure


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

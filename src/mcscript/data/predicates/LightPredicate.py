from typing import Tuple

from src.mcscript.data import getDictionaryResource
from src.mcscript.data.Commands import stringFormat
from src.mcscript.data.predicates.PredicateGenerator import PredicateGenerator
from src.mcscript.utils.FileStructure import FileStructure


class LightPredicate(PredicateGenerator):
    """
    Generates Predicates to test for the light level.
    This is done by a simple linear search (so that only one function file is necessary)
    """

    def generate(self, fileStructure: FileStructure) -> Tuple[str, ...]:
        predicate = getDictionaryResource("DefaultFiles.txt")["predicate_light"]
        predicates = []
        for i in range(16):
            name = f"predicate_light_{i}"
            predicates.append(name)
            fileStructure.pushFile(name + ".json")
            fileStructure.get().write(stringFormat(predicate, light=i))
            fileStructure.popFile()
        return tuple(predicates)

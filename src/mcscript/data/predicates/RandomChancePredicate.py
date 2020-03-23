from typing import Tuple

from src.mcscript.data import getDictionaryResource
from src.mcscript.data.Commands import stringFormat
from src.mcscript.data.predicates.PredicateGenerator import PredicateGenerator
from src.mcscript.utils.FileStructure import FileStructure


class RandomChancePredicate(PredicateGenerator):
    """
    This default dynamic predicates that return true with a custom chance.
    """

    def __init__(self, chance: float):
        super().__init__()
        self.chance = chance

    def generate(self, fileStructure: FileStructure) -> Tuple[str, ...]:
        data = stringFormat(getDictionaryResource("DefaultFiles.txt")["predicate_random_chance"], chance=self.chance)
        chance_str = str(self.chance).replace(".", "_")
        name = f"predicate_random_chance_{chance_str}"
        fileStructure.pushFile(name + ".json")
        fileStructure.get().write(data)
        fileStructure.popFile()

        return name,

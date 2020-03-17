from typing import Dict

from src.mcscript.data import getDictionaryResource
from src.mcscript.data.Commands import stringFormat
from src.mcscript.data.minecraftData import features
from src.mcscript.data.minecraftData.features import Feature
from src.mcscript.data.predicates.PredicateGenerator import PredicateGenerator
from src.mcscript.utils.FileStructure import FileStructure


class FeaturePredicate(PredicateGenerator):
    def generate(self, fileStructure: FileStructure) -> Dict[Feature, str]:
        predicate = getDictionaryResource("DefaultFiles.txt")["predicate_feature"]
        predicates: Dict[Feature, str] = {}

        for feature in features.getFeatures():
            name = f"predicate_feature_{feature.name}"
            predicates[feature] = name
            fileStructure.pushFile(name + ".json")
            fileStructure.get().write(stringFormat(predicate, feature=feature.name))
            fileStructure.popFile()

        return predicates

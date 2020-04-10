from typing import Dict

from mcscript.data import getDictionaryResource
from mcscript.data.commands import stringFormat
from mcscript.data.minecraftData import features
from mcscript.data.minecraftData.features import Feature
from mcscript.data.predicates.predicateGenerator import PredicateGenerator
from mcscript.utils.FileStructure import FileStructure


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

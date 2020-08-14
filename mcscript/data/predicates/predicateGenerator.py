from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Tuple

from mcscript.data import getDictionaryResource


class PredicateGenerator(ABC):
    """
    base class for predicate generators.
    """

    @abstractmethod
    def generate(self, fileStructure: FileStructure) -> Tuple[str, ...]:
        """
        Generates the predicate files in the fileStructure object.
        :param fileStructure: the FileStructure
        :return: a list of the names of the predicate functions, without extension
        """""


class SimplePredicateGenerator(PredicateGenerator):
    def __init__(self, *keys):
        self.keys = keys

    def generate(self, fileStructure: FileStructure) -> Tuple[str, ...]:
        data = getDictionaryResource("DefaultFiles.txt")
        for key in self.keys:
            fileStructure.pushFile(f"{key}.json")
            fileStructure.get().write(data[key])
            fileStructure.popFile()
        return self.keys

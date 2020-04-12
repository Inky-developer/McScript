from typing import Iterator

from mcscript.data import defaultEnums
from mcscript.lang.builtins.builtins import BuiltinFunction
from mcscript.lang.resource.base.ResourceType import ResourceType


def getAllBuiltins() -> Iterator[str]:
    for builtin in BuiltinFunction.functions:
        yield builtin.name()


def getAllEnums() -> Iterator[str]:
    for enum in defaultEnums.ENUMS:
        yield enum


def getAllTypes() -> Iterator[str]:
    for resourceType in ResourceType:
        if isinstance(resourceType.value, str):
            yield resourceType.value


if __name__ == '__main__':
    print('", "'.join(sorted(getAllBuiltins())))
    print(" ".join(sorted(getAllTypes())))
    print('", "'.join(sorted(getAllEnums())))

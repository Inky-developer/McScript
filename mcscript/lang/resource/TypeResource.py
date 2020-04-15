from __future__ import annotations

from enum import Flag, auto
from inspect import isclass

from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType


class TypeModifiers(Flag):
    CONST = auto()
    PRIVATE = auto()

    @classmethod
    def fromString(cls, string: str) -> TypeModifiers:
        return TypeModifiers[string.strip().upper()]


class TypeResource(ValueResource):
    def __init__(self, value, isStatic=True, *stringFlags):
        super().__init__(value, isStatic)

        self.modifierFlags = TypeModifiers(sum(TypeModifiers.fromString(i).value for i in stringFlags if i is not None))

    def embed(self) -> str:
        return f"Type[{self.value.type().name}]"

    def typeCheck(self) -> bool:
        """
        Accepts a subclass of resource and structs.
        """
        return (isclass(self.value) and issubclass(self.value, Resource)) or isinstance(self.value, StructResource)

    @classmethod
    def fromType(cls, resourceType: ResourceType) -> TypeResource:
        return TypeResource(Resource.getResourceClass(resourceType))

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.TYPE

    def __repr__(self):
        return self.embed()

from inspect import isclass

from src.mcscript.lang.resource.StructResource import StructResource
from src.mcscript.lang.resource.base.ResourceBase import ValueResource, Resource
from src.mcscript.lang.resource.base.ResourceType import ResourceType


class TypeResource(ValueResource):
    def embed(self) -> str:
        return f"Type[{self.value.type().name}]"

    def typeCheck(self) -> bool:
        """
        Accepts a subclass of resource and structs.
        """
        return (isclass(self.value) and issubclass(self.value, Resource)) or isinstance(self.value, StructResource)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.TYPE

    def __repr__(self):
        return self.embed()

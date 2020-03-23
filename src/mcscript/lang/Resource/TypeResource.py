from src.mcscript.lang.Resource.ResourceBase import ValueResource, Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class TypeResource(ValueResource):
    def embed(self) -> str:
        return f"Type[{self.value}]"

    def typeCheck(self) -> bool:
        return issubclass(self.value, Resource)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.TYPE

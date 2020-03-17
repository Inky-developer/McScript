from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class SelectorResource(ValueResource):
    """
    Holds a minecraft selector
    """

    def embed(self) -> str:
        return self.value

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.SELECTOR

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

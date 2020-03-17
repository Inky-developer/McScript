from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class AddressResource(ValueResource):
    """
    Holds the address for a scoreboard player
    """
    _hasStaticValue = False

    @staticmethod
    def type():
        return ResourceType.ADDRESS

    def embed(self) -> str:
        return self.value

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

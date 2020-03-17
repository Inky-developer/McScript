from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class NbtAddressResource(ValueResource):
    """
    Holds the address for a scoreboard player
    """
    _hasStaticValue = False

    @staticmethod
    def type():
        return ResourceType.NBT_ADDRESS

    def embed(self) -> str:
        return self.value

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

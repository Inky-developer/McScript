from mcscript.lang.resource.base.ResourceBase import ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.resources import DataPath


class NbtAddressResource(ValueResource):
    """
    Holds the address for a scoreboard player
    """
    _hasStaticValue = False

    def __init__(self, value: DataPath):
        super().__init__(value, True)

    @staticmethod
    def type():
        return ResourceType.NBT_ADDRESS

    def embed(self) -> str:
        return str(self.static_value)

    def typeCheck(self) -> bool:
        return isinstance(self.static_value, DataPath)

    def __getitem__(self, item: int):
        if not isinstance(item, int):
            return NotImplemented
        return NbtAddressResource(self.static_value.last_element_indexed(int))

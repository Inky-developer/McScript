from mcscript.lang.resource.base.ResourceBase import ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType


class NbtAddressResource(ValueResource):
    """
    Holds the address for a scoreboard player
    """
    _hasStaticValue = False

    def __init__(self, value: str):
        super().__init__(value, True)
        *self.address, self.name = value.split(".")
        self.address = ".".join(self.address)

    @staticmethod
    def type():
        return ResourceType.NBT_ADDRESS

    def embed(self) -> str:
        return self.value

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

    def __add__(self, other):
        if not isinstance(other, NbtAddressResource):
            return NotImplemented
        return NbtAddressResource(f"{self.embed()}.{other.embed()}")

    def __getitem__(self, item):
        if not isinstance(item, int):
            return NotImplemented
        return NbtAddressResource(f"{self.embed()}[{item}]")

from src.mcscript.Exceptions import McScriptNameError
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import ObjectResource, Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class EnumResource(ObjectResource):
    """
    Is an enum. All values are numbers
    """

    def __init__(self, *properties, **namedProperties):
        """
        Sets its enumMembers.
        properties is a list of members, each member gets as the value its index
        """
        super().__init__()
        self.namespace.update({key: NumberResource(value, True) for value, key in enumerate(properties)})
        self.namespace.update(namedProperties)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.ENUM

    def getAttribute(self, name: str) -> Resource:
        try:
            return self.namespace[name]
        except KeyError:
            raise McScriptNameError(
                f"Member {name} of enum does not exist. Members: {', '.join(i for i in self.namespace)}")

    def toString(self) -> str:
        raise TypeError()

    def toNumber(self) -> int:
        raise TypeError()

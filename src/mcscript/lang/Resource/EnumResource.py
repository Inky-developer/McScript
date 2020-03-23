from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.Exceptions import McScriptNameError, McScriptArgumentsError
from src.mcscript.lang.Resource.BooleanResource import BooleanResource
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import ObjectResource, Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.Resource.StringResource import StringResource

if TYPE_CHECKING:
    from src.mcscript import CompileState


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
        self.namespace.namespace.update({key: NumberResource(value, True) for value, key in enumerate(properties)})
        self.namespace.namespace.update(namedProperties)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.ENUM

    def getAttribute(self, name: str) -> Resource:
        try:
            return self.namespace[name]
        except KeyError:
            raise McScriptNameError(
                f"Member {name} of enum does not exist. Members: {', '.join(i for i in self.namespace)}")

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        """ returns the name of the member with the given value"""
        if len(parameters) != 1:
            raise McScriptArgumentsError(f"Enum must be called with exactly one parameter <index>")
        parameter = compileState.load(parameters[0])
        try:
            parameter = parameter.toNumber()
        except TypeError:
            raise McScriptArgumentsError(
                "Enum must be called with an argument that is static and can be converted to a number.")
        for key in self.namespace:
            if self.namespace[key].toNumber() == parameter:
                return StringResource(key, True)
        raise McScriptArgumentsError(f"Enum {repr(self)} has no member with a value of {parameter}")

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        """ returns true if this enum contains at least one member"""
        return BooleanResource.TRUE if self.namespace.namespace else BooleanResource.FALSE

    def toString(self) -> str:
        raise TypeError()

    def toNumber(self) -> int:
        raise TypeError()

from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptArgumentsError
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class EnumResource(ObjectResource):
    """
    Is an enum. All values are numbers
    """

    def __init__(self, *properties, **valueProperties):
        """
        Sets its enumMembers.
        properties is a list of members, each member gets as the value its index
        """
        super().__init__()
        self.namespace.namespace.update({key: NumberResource(value, True) for value, key in enumerate(properties)})
        self.namespace.namespace.update(valueProperties)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.ENUM

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        try:
            return self.namespace[name]
        except KeyError:
            raise AttributeError()

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        """ returns the name of the member with the given value"""
        if len(parameters) != 1:
            raise McScriptArgumentsError(f"Enum must be called with exactly one parameter <index>", compileState)
        parameter = compileState.load(parameters[0])
        try:
            parameter = parameter.toNumber()
        except TypeError:
            raise McScriptArgumentsError(
                "Enum must be called with an argument that is static and can be converted to a number.",
                compileState
            )
        for key in self.namespace:
            if self.namespace[key].toNumber() == parameter:
                return StringResource(key, True)
        raise McScriptArgumentsError(f"Enum {repr(self)} has no member with a value of {parameter}", compileState)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        """ returns true if this enum contains at least one member"""
        return BooleanResource.TRUE if self.namespace.namespace else BooleanResource.FALSE

    def toString(self) -> str:
        raise TypeError()

    def toNumber(self) -> int:
        raise TypeError()

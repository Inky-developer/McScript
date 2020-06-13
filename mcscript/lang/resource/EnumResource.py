from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.exceptions.compileExceptions import McScriptArgumentsError, McScriptAttributeError
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter


class EnumResource(ObjectResource):
    """
    Is an enum.
    """

    def __init__(self, *properties, **valueProperties):
        """
        Sets its enumMembers.
        properties is a list of members, each member gets as the value its index
        """
        super().__init__()
        for index, name in enumerate(properties):
            self.context.add_var(name, NumberResource(index, True))
        # self.context.namespace.update({key: NumberResource(value, True) for value, key in enumerate(properties)})

        _used_values = set(range(len(properties)))

        for key in valueProperties:
            resource = valueProperties[key]
            if not isinstance(resource, ValueResource):
                raise TypeError(f"Invalid value for enum member {key}: {resource}")
            if resource.value in _used_values:
                other, = filter(lambda x: self.context[x].value == resource.value, self.context)
                raise ValueError(f"key '{key}' does not have a unique value of {resource.value} which is already "
                                 f"defined for '{other}'")
            self.context.add_var(key, resource)
            _used_values.add(resource.value)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.ENUM

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        try:
            return self.context.namespace[name].resource
        except KeyError:
            raise McScriptAttributeError(f"Unknown member {name} of enum.\n"
                                         f"Expected one of: {', '.join(i for i in self.context)}", compileState)

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        """ returns the name of the member with the given value"""
        # ToDo implement this for non-static values
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
        for key in self.context.namespace:
            if self.context.namespace[key].resource.toNumber() == parameter:
                return StringResource(key, True)
        raise McScriptArgumentsError(f"Enum {repr(self)} has no member with a value of {parameter}", compileState)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        """ returns true if this enum contains at least one member"""
        return BooleanResource.TRUE if self.context.namespace else BooleanResource.FALSE

    def toTextJson(self, compileState: CompileState, formatter: ResourceTextFormatter) -> list:
        parameters = []
        for value in self.context:
            parameters.append(value)
            parameters.append("=")
            parameters.append(self.context[value])
            parameters.append(", ")
        return formatter.createFromResources("Enum(", *parameters[:-1], ")")

    def toString(self) -> str:
        raise TypeError()

    def toNumber(self) -> int:
        raise TypeError()

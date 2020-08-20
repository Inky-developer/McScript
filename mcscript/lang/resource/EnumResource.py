from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.exceptions.exceptions import McScriptUndefinedAttributeError
from mcscript.lang.atomic_types import Enum, Type
from mcscript.lang.resource.IntegerResource import IntegerResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter


class EnumResource(ObjectResource):
    """
    Is an enum.
    Currently enums are quite simple and boring, they can just store numbers.
    Maybe this will change (rust-style enums would be great)
    """

    def __init__(self, *properties, **valueProperties):
        """
        Sets its enumMembers.
        properties is a list of members, each member gets as the value its index
        """
        super().__init__()
        for index, name in enumerate(properties):
            self.public_namespace[name] = IntegerResource(index, None)

        _used_values = set(range(len(properties)))

        for key in valueProperties:
            resource = valueProperties[key]
            if not isinstance(resource, ValueResource):
                raise TypeError(key, resource)
            self.public_namespace[key] = resource
            _used_values.add(resource.static_value)

    def type(self) -> Type:
        return Enum

    def supports_scoreboard(self) -> bool:
        return False

    # We could technically support this
    def supports_storage(self) -> bool:
        return False

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        try:
            return self.public_namespace[name]
        except KeyError:
            raise McScriptUndefinedAttributeError(self, name, compileState)

    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> list:
        parameters = []
        for value in self.public_namespace:
            parameters.append(value)
            parameters.append("=")
            parameters.append(self.public_namespace[value])
            parameters.append(", ")
        return formatter.createFromResources("Enum(", *parameters[:-1], ")")

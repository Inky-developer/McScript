from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.exceptions.compileExceptions import McScriptAttributeError
from mcscript.lang.atomic_types import Enum, Type
from mcscript.lang.resource.IntegerResource import IntegerResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource, ValueResource

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
            self.context.add_var(name, IntegerResource(index, None))
        # self.context.namespace.update({key: NumberResource(value, True) for value, key in enumerate(properties)})

        _used_values = set(range(len(properties)))

        for key in valueProperties:
            resource = valueProperties[key]
            if not isinstance(resource, ValueResource):
                raise TypeError(f"Invalid value for enum member {key}: {resource}")
            if resource.static_value in _used_values:
                other, = filter(lambda x: self.context[x].value == resource.value, self.context)
                raise ValueError(
                    f"key '{key}' does not have a unique value of {resource.static_value} which is already "
                    f"defined for '{other}'")
            self.context.add_var(key, resource)
            _used_values.add(resource.static_value)

    def type(self) -> Type:
        return Enum

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        try:
            return self.context.namespace[name].resource
        except KeyError:
            raise McScriptAttributeError(f"Unknown member {name} of enum.\n"
                                         f"Expected one of: {', '.join(i for i in self.context)}", compileState)

    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> list:
        parameters = []
        for value in self.context:
            parameters.append(value)
            parameters.append("=")
            parameters.append(self.context[value])
            parameters.append(", ")
        return formatter.createFromResources("Enum(", *parameters[:-1], ")")

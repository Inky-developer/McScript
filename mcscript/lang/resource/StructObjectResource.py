from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Union, List

from mcscript.exceptions.compileExceptions import McScriptTypeError, McScriptArgumentsError, McScriptAttributeError
from mcscript.lang.Type import Type
from mcscript.lang.resource.StructResource import StructResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource
from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class StructObjectResource(ObjectResource):
    """
    The object representation of a struct.
    A struct is initialized with keyword parameters that correspond with the declared fields.
    """

    def __init__(self, struct: StructResource, compile_state: CompileState, keyword_parameters: Dict[str, Resource]):
        super().__init__()
        self.struct = struct

        self.initialize_struct(compile_state, keyword_parameters)

    def initialize_struct(self, compile_state: CompileState, keyword_parameters: Dict[str, Resource]):
        """ Initializes the struct and checks that the attributes get correctly set. """
        definitions = self.struct.getDeclaredVariables()
        used_parameters = set()

        for name, value in keyword_parameters.items():
            # parameter not in definition
            if name not in definitions:
                raise McScriptArgumentsError(f"Unexpected attribute: {name}", compile_state)
            # wrong parameter type
            if not value.type().matches(definitions[name]):
                raise McScriptTypeError(
                    f"Expected type {{{definitions[name]}}} but got {{{value.type()}}} for attribute {name}",
                    compile_state)
            # parameter already specified
            if name in used_parameters:
                raise McScriptArgumentsError(f"Attribute {name} was specified twice", compile_state)

            used_parameters.add(name)
            self.public_namespace[name] = value

        # parameter not specified
        not_specified_parameters = used_parameters.symmetric_difference(definitions.keys())
        if not_specified_parameters:
            raise McScriptArgumentsError(
                f"At least one attribute was not specified. Missing {not_specified_parameters}", compile_state)

    def setAttribute(self, compileState: CompileState, name: str, value: Resource):
        expected_type = self.struct.getDeclaredVariables()[name]
        if name not in self.public_namespace:
            raise McScriptAttributeError(f"Cannot set attribute {name} because it does not exist", compileState)
        if not value.type().matches(expected_type):
            raise McScriptAttributeError(
                f"Expected {name} to be of type {{{expected_type}}}, but got type {{{value.type()}}}", compileState)
        self.public_namespace[name] = value

    def type(self) -> Type:
        return self.struct.object_type

    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Union[Dict, List, str]:
        components = [f"{self.struct.name}{{"]

        is_first = True
        for name, resource in self.public_namespace.items():
            if is_first:
                components.append(f"{name}: ")
                is_first = False
            else:
                components.append(f", {name}: ")
            components.append(resource)

        components.append("}")
        return formatter.createFromResources(*components)

    def __repr__(self):
        return f"Object<{self.struct.name}>"

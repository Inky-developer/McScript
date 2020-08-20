from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Union, List

from mcscript.exceptions.exceptions import (McScriptArgumentError, McScriptUnexpectedTypeError,
                                            McScriptUndefinedAttributeError)
from mcscript.lang.Type import Type
from mcscript.lang.resource.FunctionResource import FunctionResource
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
                raise McScriptArgumentError(f"Unexpected attribute: {name}", compile_state)
            # wrong parameter type
            if not value.type().matches(definitions[name]):
                raise McScriptUnexpectedTypeError(name, value.type(), definitions[name], compile_state)
            # parameter already specified
            if name in used_parameters:
                raise McScriptArgumentError(f"Attribute {name} was specified twice", compile_state)

            used_parameters.add(name)
            value.is_variable = True
            self.public_namespace[name] = value

        # parameter not specified
        not_specified_parameters = used_parameters.symmetric_difference(definitions.keys())
        if not_specified_parameters:
            raise McScriptArgumentError(
                f"At least one attribute was not specified. Missing {not_specified_parameters}", compile_state)

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        try:
            return super().getAttribute(compileState, name)
        except KeyError:
            result = self.struct.getAttribute(compileState, name)
            # return a method instead of a function
            if isinstance(result, FunctionResource) and result.function_signature.is_method:
                return result.make_method(self)
            return result

    def setAttribute(self, compile_state: CompileState, name: str, value: Resource):
        expected_type = self.struct.getDeclaredVariables().get(name, None)
        if name not in self.public_namespace:
            raise McScriptUndefinedAttributeError(self, name, compile_state)
        if not value.type().matches(expected_type):
            raise McScriptUnexpectedTypeError(name, value.type(), expected_type, compile_state)
        self.public_namespace[name] = value
        value.is_variable = True

    def type(self) -> Type:
        return self.struct.object_type

    def supports_scoreboard(self) -> bool:
        return all(i.supports_scoreboard() for i in self.public_namespace.values())

    def supports_storage(self) -> bool:
        return all(i.supports_storage for i in self.public_namespace.values())

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

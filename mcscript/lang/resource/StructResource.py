from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.Context import Context
    from mcscript.compiler.CompileState import CompileState


class StructResource(ObjectResource):
    """
    The resource for a struct.
    Holds value definitions and functions
    """

    def __init__(self, name: str, ownContext: Context):
        super().__init__()
        self.context = ownContext
        self.name = name

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        """
        Creates a new object of type `StructObjectResource`

        Args:
            compileState: the compile state
            *parameters: the parameters for the initialization
            **keywordParameters: keyword parameters for the initialization. Currently not used

        Returns:
            A new `ObjectResource`
        """
        from mcscript.lang.resource.StructObjectResource import StructObjectResource
        # ToDo: Create dedicated struct creation syntax
        assert not keywordParameters

        declared_vars = self.getDeclaredVariables()
        keyword_parameters = dict(zip(declared_vars.keys(), parameters))

        return StructObjectResource(self, compileState, keyword_parameters)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.STRUCT

    def getDeclaredVariables(self) -> Dict[str, ResourceType]:
        """ Returns all declared type resources """
        return {name: value.resource.static_value for name, value in self.context.namespace.items() if
                isinstance(value.resource, TypeResource)}

    def __repr__(self):
        return f"Struct<{self.name}>"

from __future__ import annotations

from typing import List, TYPE_CHECKING, Tuple

from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource, Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.Context import Context
    from mcscript.lang.resource.TypeResource import TypeResource
    from mcscript.compiler.CompileState import CompileState


class StructResource(ObjectResource):
    """
    The resource for a struct. The namespace should only contain TypeResources
    """

    def __init__(self, name: str, ownContext: Context):
        super().__init__(ownContext)
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
        return StructObjectResource(self, compileState, *parameters, **keywordParameters)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.STRUCT

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return BooleanResource.TRUE

    def toNumber(self) -> int:
        raise TypeError

    def toString(self) -> str:
        return str(self)

    def getDeclaredVariables(self) -> List[Tuple[str, TypeResource]]:
        """ Returns all declared type resources """
        return [(i, self.context.namespace[i].resource) for i in self.context.namespace if
                self.context.namespace[i].resource.type() == ResourceType.TYPE]

    def __str__(self):
        return f"Struct<{self.name}>"

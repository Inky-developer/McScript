from __future__ import annotations

from typing import TYPE_CHECKING, Tuple, List

from src.mcscript.compiler import Namespace
from src.mcscript.lang.Resource.BooleanResource import BooleanResource
from src.mcscript.lang.Resource.ResourceBase import ObjectResource, Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.Resource.TypeResource import TypeResource

if TYPE_CHECKING:
    from src.mcscript.compiler.CompileState import CompileState


class StructResource(ObjectResource):
    """
    The resource for a struct. The namespace should only contain TypeResources
    """

    def __init__(self, name: str, ownNamespace: Namespace):
        super().__init__(ownNamespace)
        self.name = name

    def operation_call(self, compileState: CompileState, *parameters: Resource,
                       **keywordParameters: Resource) -> Resource:
        """
        Creates a new object of type StructObjectResource
        :param compileState: the compile state
        :param parameters: the parameters of the initialization
        :param keywordParameters: the keyword parameters for the initialization, currently unused
        :return: the new object
        """
        from src.mcscript.lang.Resource.StructObjectResource import StructObjectResource
        return StructObjectResource(self, compileState, *parameters, **keywordParameters)

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.STRUCT

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return BooleanResource.TRUE

    def toNumber(self) -> int:
        raise TypeError

    def toString(self) -> str:
        raise TypeError

    def getDeclaredVariables(self) -> List[Tuple[str, TypeResource]]:
        """ Returns all declared type resources """
        return [(i, self.namespace[i]) for i in self.namespace.namespace if
                self.namespace[i].type() == ResourceType.TYPE]

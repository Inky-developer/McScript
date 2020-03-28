from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union, Type

from src.mcscript.compiler.NamespaceType import NamespaceType
from src.mcscript.data.builtins.builtins import BuiltinFunction
from src.mcscript.lang.Resource.NbtAddressResource import NbtAddressResource
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource
from src.mcscript.utils.NamespaceBase import NamespaceBase

if TYPE_CHECKING:
    from src.mcscript.lang.Resource.FunctionResource import Function


class Namespace(NamespaceBase[Resource]):
    def __init__(self, previous: Optional[NamespaceBase] = None, namespaceType: NamespaceType = NamespaceType.OTHER):
        super().__init__(previous)
        self.variableFmt = f"{self.index}_{{}}" if self.index != 0 else "{}"

        self.namespaceType = namespaceType
        self.returnedResource: Optional[Resource] = None

    def setPredecessor(self, predecessor: NamespaceBase):
        super().setPredecessor(predecessor)
        self.variableFmt = f"{self.index}_{{}}" if self.index != 0 else "{}"

    def addVar(self, identifier: str, resourceClass: Type[ValueResource]) -> ValueResource:
        """
        Adds a variable to the current namespace even if there exists already one in a predecessor namespace.
        :param identifier: the identifier of the variable in code
        :param resourceClass: the class of the resource to be added
        :return: the resource
        """
        if identifier in self.namespace:
            raise ValueError(f"Cannot add variable {identifier} to this namespace, because it already exists.")
        stack = NbtAddressResource(self.variableFmt.format(identifier))
        resource = resourceClass(stack, False)
        self.namespace[identifier] = resource
        return resource

    def setVar(self, identifier: str, var: Resource):
        # if the variable already exists override the old one
        namespace = self
        while namespace:
            if identifier in namespace.namespace:
                namespace[identifier] = var
            namespace = namespace.predecessor if namespace.predecessor is not None else None

        self.namespace[identifier] = var

    def __setitem__(self, key, value):
        self.namespace[key] = value

    def addFunction(self, function: Union[Function, BuiltinFunction]):
        self.namespace[function.name()] = function

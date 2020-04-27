from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Type, Union

from mcscript.compiler.NamespaceType import NamespaceType
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.utils.Address import Address
from mcscript.utils.NamespaceBase import NamespaceBase

if TYPE_CHECKING:
    from mcscript.lang.builtins.builtins import BuiltinFunction
    from mcscript.lang.resource.base.FunctionResource import FunctionResource


class Namespace(NamespaceBase[Resource]):
    def __init__(self, identification: int, namespaceType: NamespaceType, previous: Optional[Namespace] = None):
        super().__init__(previous)
        self.id = identification

        self.variableFmt = f"{self.id}_{{}}" if self.id != 0 else "{}"

        self.expressionStack = Address(f".exp_{self.id}_{{}}", previous.expressionStack.value if previous else 0)

        self.namespaceType = namespaceType
        self.returnedResource: Resource = NullResource()

    def isContextStatic(self) -> bool:
        """
        Returns true if the namespaceType of this namespace and all predecessors is static
        """
        if self.predecessor is None:
            return self.namespaceType.hasStaticContext

        self.predecessor: Namespace
        return self.namespaceType.hasStaticContext and self.predecessor.isContextStatic()

    def setPredecessor(self, predecessor: Namespace):
        super().setPredecessor(predecessor)
        self.variableFmt = f"{self.index}_{{}}" if self.index != 0 else "{}"

    def addVar(self, identifier: str, resourceClass: Type[ValueResource]) -> ValueResource:
        """
        Adds a variable to the current namespace even if there exists already one in a predecessor namespace.

        Parameters:
            identifier: the identifier of the variable in code
            resourceClass: the class of the resource to be added

        Returns:
            the resource
        """
        if identifier in self.namespace:
            raise ValueError(f"Cannot add variable {identifier} to this namespace, because it already exists.")
        stack = NbtAddressResource(self.variableFmt.format(identifier))
        resource = resourceClass(stack, False)
        self.namespace[identifier] = resource
        return resource

    def setVar(self, identifier: str, var: Resource):
        """
        Sets a variable. If this variable is defined in an older namespace, override it.

        Args:
            identifier: the name of the variable
            var: the value of the variable
        """
        # if the variable already exists override the old one
        namespace = self
        while namespace:
            if identifier in namespace.namespace:
                namespace[identifier] = var
            namespace = namespace.predecessor if namespace.predecessor is not None else None

        self.namespace[identifier] = var

    def __setitem__(self, key, value):
        self.namespace[key] = value

    def addFunction(self, function: Union[BuiltinFunction, FunctionResource]):
        self.namespace[function.name()] = function

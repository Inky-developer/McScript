from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Union

from src.mcscript.data.builtins.builtins import BuiltinFunction
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource
from src.mcscript.utils.NamespaceBase import NamespaceBase

if TYPE_CHECKING:
    from src.mcscript.lang.Resource.FunctionResource import Function


class Namespace(NamespaceBase[Resource]):
    def __init__(self, previous: Optional[NamespaceBase], index: int):
        super().__init__(previous, index)
        self.variableFmt = f"{index}_{{}}" if index != 0 else "{}"

    # def add(self, varName: str) -> Resource:
    #     # if the variable already exists ina previous namespace returns its address to allow overrides
    #     if self.predecessor and varName in self.predecessor:
    #         return self.predecessor[varName]
    #     address = self.variableFmt.format(varName)
    #     self.namespace[str(varName)] = AddressResource(address, True)
    #     return self.namespace[str(varName)]

    def setVar(self, identifier: str, var: ValueResource):
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

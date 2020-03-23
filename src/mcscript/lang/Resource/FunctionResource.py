from __future__ import annotations

from typing import List, Type, Tuple, TYPE_CHECKING

from lark import Token

from src.mcscript.compiler import Namespace
from src.mcscript.lang.Resource.BooleanResource import BooleanResource
from src.mcscript.lang.Resource.ResourceBase import ObjectResource, Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState

Parameter = Tuple[Token, Type[Resource]]


class Function(ObjectResource):
    def __init__(self, function_name: str, returnType: Type[Resource], parameters: List[Parameter],
                 namespace: Namespace, blockName: str):
        super().__init__()
        self._name = function_name
        self.returnType = returnType
        self.parameters = parameters

        self.namespace = namespace
        self.blockName = blockName

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.FUNCTION

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return BooleanResource.TRUE

    def toNumber(self) -> int:
        raise TypeError()

    def toString(self) -> str:
        return self.blockName

    def name(self):
        return self._name

    def __repr__(self):
        return f"fun {self.name()}({', '.join(f'{name}: {res.type().value}' for name, res in self.parameters)})"

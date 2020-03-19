from typing import List, Type, Optional

from lark import Tree

from src.mcscript.compiler import Namespace
from src.mcscript.lang.Resource.ResourceBase import ObjectResource, Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class Function(ObjectResource):
    def __init__(self, function_name: str, returnType: Type[Resource], parameters: List[Tree]):
        super().__init__()
        self._name = function_name
        self.returnType = returnType
        self.parameters = parameters

        # not optional, will beset after init
        self.namespace: Optional[Namespace] = None
        self.blockName: Optional[str] = None

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.FUNCTION

    def toNumber(self) -> int:
        raise TypeError()

    def toString(self) -> str:
        return self.blockName

    def name(self):
        return self._name

    def __repr__(self):
        return f"Function_{self.name()}({', '.join(str(i) for i in self.parameters)})"

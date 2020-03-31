from __future__ import annotations

from tkinter.tix import Tree
from typing import List, Tuple, TYPE_CHECKING

from src.mcscript.lang.resource.BooleanResource import BooleanResource
from src.mcscript.lang.resource.TypeResource import TypeResource
from src.mcscript.lang.resource.base.ResourceBase import ObjectResource
from src.mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState

Parameter = Tuple[str, TypeResource]


class FunctionResource(ObjectResource):
    """
    Base class for functions.
    """
    isDefault = False

    def __init__(self, name: str, parameters: List[Parameter], returnType: TypeResource, block: Tree):
        super().__init__()
        self._name = name
        self.returnType = returnType
        self.parameters = parameters
        self.block = block

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.FUNCTION

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return BooleanResource.TRUE

    def name(self):
        return self._name

    def toNumber(self) -> int:
        raise TypeError()

    def toString(self) -> str:
        return self.name()

    def __repr__(self):
        return f"fun {self.name()}({', '.join(f'{name}: {res.value.type().value}' for name, res in self.parameters)})"

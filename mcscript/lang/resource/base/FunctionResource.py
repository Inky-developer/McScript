from __future__ import annotations

from functools import cached_property
from tkinter.tix import Tree
from typing import List, TYPE_CHECKING, Tuple

from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.TypeResource import TypeResource
from mcscript.lang.resource.base.ResourceBase import ObjectResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.functionSignature import FunctionParameter, FunctionSignature

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState

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

    @cached_property
    def signature(self) -> FunctionSignature:
        parameters = []
        for name, type_ in self.parameters:
            parameters.append(FunctionParameter(
                name,
                type_
            ))

        return FunctionSignature(
            self,
            parameters,
            self.returnType.value.type(),
            inline=self.inline()
        )

    @staticmethod
    def inline() -> bool:
        return False

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
        return self.signature.signature_string()

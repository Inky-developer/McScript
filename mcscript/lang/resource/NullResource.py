from __future__ import annotations

from typing import Any, TYPE_CHECKING

from mcscript.lang.resource.base.ResourceBase import ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


# noinspection PyUnusedLocal
class NullResource(ValueResource):
    requiresInlineFunc = False

    def __init__(self, value: Any = None, isStatic: bool = True):
        """
        parameters are discarded
        """
        super().__init__(None, True)

    def embed(self) -> str:
        return "null"

    def typeCheck(self) -> bool:
        return True

    def copy(self, target: ValueResource, compileState: CompileState) -> NullResource:
        return NullResource()

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NULL

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> NullResource:
        # noinspection PyTypeChecker
        return compileState.currentContext().add_var(identifier, NullResource())

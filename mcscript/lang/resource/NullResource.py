from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from mcscript.lang.resource.base.ResourceBase import ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


# noinspection PyUnusedLocal
class NullResource(ValueResource[None]):
    requiresInlineFunc: ClassVar[bool] = False

    def __init__(self):
        """
        parameters are discarded
        """
        super().__init__(None, None)

    def copy(self, target: ValueResource, compileState: CompileState) -> NullResource:
        return NullResource()

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NULL

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> NullResource:
        # noinspection PyTypeChecker
        return compileState.currentContext().add_var(identifier, NullResource())

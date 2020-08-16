from __future__ import annotations

from typing import TYPE_CHECKING, Type

from mcscript.lang.atomic_types import Null
from mcscript.lang.resource.base.ResourceBase import ValueResource, Resource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class NullResource(ValueResource[None]):
    def __init__(self, _static_value=None, _scoreboard_value=None):
        """
        parameters are discarded
        """
        super().__init__(0, None)

    def copy(self, target: ValueResource, compileState: CompileState) -> NullResource:
        return NullResource()

    def type(self) -> Type:
        return Null

    @classmethod
    def createEmptyResource(cls, identifier: str, compileState: CompileState) -> Resource:
        return compileState.currentContext().add_var(identifier, NullResource())

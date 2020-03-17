from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.data.Commands import Command
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class FixedNumberVariableResource(ValueResource):
    """
    Used when a fixed number is stored as a variable on a nbt storage
    """
    isDefault = False

    def embed(self) -> str:
        return str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, AddressResource) and not self.isStatic

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.FIXED_POINT

    def loadToScoreboard(self, compileState: CompileState) -> FixedNumberResource:
        stack = compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_VARIABLE(
            stack=stack,
            var=self.embed()
        ))
        return FixedNumberResource(stack, False)

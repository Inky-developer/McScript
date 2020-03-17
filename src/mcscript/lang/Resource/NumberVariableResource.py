from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.data.Commands import Command
from src.mcscript.lang.Resource.AddressResource import AddressResource
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript.compiler.CompileState import CompileState


class NumberVariableResource(ValueResource):
    """
    Used when a number is stored as a variable
    """
    _hasStaticValue = False
    isDefault = False

    def embed(self) -> str:
        return str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, AddressResource) and not self.isStatic

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NUMBER

    def loadToScoreboard(self, compileState: CompileState) -> NumberResource:
        stack = compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_VARIABLE(
            stack=stack,
            var=self.embed()
        ))
        return NumberResource(stack, False)

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from mcscript.ir.components import StoreFastVarNode
from mcscript.lang.resource.base.ResourceBase import MinecraftDataStorage, Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.resources import ScoreboardValue, DataPath

if TYPE_CHECKING:
    from typing import Any
    from mcscript.compiler.CompileState import CompileState


class VariableResource(ValueResource, ABC):
    """
    Represents a valueResource on data storage.
    """
    _hasStaticValue = False
    isDefault = False
    isVariable = True
    storage = MinecraftDataStorage.STORAGE

    def __init__(self, value, isStatic: bool, static_value: Optional[Any] = None):
        super().__init__(value, isStatic)

        # if this resource is not static, but a value is for (only) this resource known
        self.static_value = static_value

    @staticmethod
    @abstractmethod
    def type() -> ResourceType:
        pass

    def typeCheck(self) -> bool:
        return isinstance(self.static_value, DataPath) and self.isStatic

    def storeToNbt(self, stack: DataPath, compileState: CompileState) -> Resource:
        return self.copy(stack, compileState)

    def _load(self, compileState: CompileState, stack: Optional[ScoreboardValue], scale=1) -> ScoreboardValue:
        stack = stack or compileState.expressionStack.next()

        # ToDo missing scale
        compileState.ir.append(StoreFastVarNode(stack, self.static_value))

        return stack

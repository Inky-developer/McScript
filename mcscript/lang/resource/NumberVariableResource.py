from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.base.VariableResource import VariableResource
from mcscript.utils.resources import ScoreboardValue

if TYPE_CHECKING:
    from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
    from mcscript.compiler.CompileState import CompileState


class NumberVariableResource(VariableResource):
    """
    Used when a number is stored as a variable
    """

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.NUMBER

    def load(self, compileState: CompileState, stack: ScoreboardValue = None) -> NumberResource:
        if self.static_value is not None:
            return NumberResource(self.static_value, True)
        stack = self._load(compileState, stack)
        return NumberResource(stack, False)

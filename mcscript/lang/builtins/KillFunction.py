from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import Command
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class KillFunction(BuiltinFunction):
    """
    parameter => [Optional=@s] target: Selector the target to kill
    Kills the target and returns how many entities were killed.
    """

    def name(self) -> str:
        return "kill"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        target: SelectorResource
        target, = parameters
        return FunctionResult(
            Command.SET_VALUE_FROM(
                stack=compileState.config.RETURN_SCORE,
                command=Command.KILL_ENTITY(target=target.embed_non_static(compileState))
            ), NumberResource(compileState.config.RETURN_SCORE, False)
        )

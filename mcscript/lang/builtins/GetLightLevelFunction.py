from __future__ import annotations

from typing import Any, TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptArgumentsError
from mcscript.data.commands import Command, ExecuteCommand, multiple_commands
from mcscript.lang.builtins.builtins import CachedFunction
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class GetLightLevel(CachedFunction):
    """
    Returns the light level at the current position.
    Range: -1..15; -1 if the function could not execute correctly, this *should* never happen.
    """

    def name(self) -> str:
        return "getLightLevel"

    def returnType(self) -> ResourceType:
        return ResourceType.NUMBER

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        if len(parameters) != 0:
            raise McScriptArgumentsError("Function getLightLevel expected no arguments.")

        stack = compileState.config.RETURN_SCORE
        commands = [Command.EXECUTE(
            sub=ExecuteCommand.IF_PREDICATE(predicate=predicate),
            command=Command.SET_VALUE(
                stack=stack,
                value=index
            )
        ) for index, predicate in enumerate(self.predicates)]
        commands.insert(0, Command.SET_VALUE(stack=stack, value=-1))
        return multiple_commands(*commands)

    def include(self, compileState: CompileState) -> Any:
        self.predicates = compileState.datapack.getUtilsDirectory().addLightPredicate()

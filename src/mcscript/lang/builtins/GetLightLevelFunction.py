from __future__ import annotations

from typing import Union, Any, TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import Command, ExecuteCommand, multiple_commands
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.builtins.builtins import CachedFunction, FunctionResult

if TYPE_CHECKING:
    from src.mcscript import CompileState


class GetLightLevel(CachedFunction):
    """
    Returns the light level at the current position.
    Range: -1..15; -1 if the function could not execute correctly, this *should* never happen.
    """

    def name(self) -> str:
        return "getLightLevel"

    def returnType(self) -> ResourceType:
        return ResourceType.NUMBER

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        if len(parameters) != 0:
            raise McScriptArgumentsError("Function getLightLevel expected no arguments.")

        commands = [Command.EXECUTE(
            sub=ExecuteCommand.IF_PREDICATE(predicate=predicate),
            command=Command.SET_VALUE(
                stack=compileState.config.RETURN_SCORE,
                value=index
            )
        ) for index, predicate in enumerate(self.predicates)]
        commands.insert(0, Command.SET_VALUE(stack=compileState.config.RETURN_SCORE, value=-1))
        return multiple_commands(*commands)

    def include(self, compileState: CompileState) -> Any:
        self.predicates = compileState.datapack.getUtilsDirectory().addLightPredicate()

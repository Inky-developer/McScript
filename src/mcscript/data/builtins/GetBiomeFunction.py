from __future__ import annotations

from typing import Union, Any, TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import Command, ExecuteCommand, multiple_commands
from src.mcscript.data.builtins.builtins import CachedFunction, FunctionResult
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class GetBiomeFunction(CachedFunction):
    """
    returns the biome id of the current biome the executor is in.
    """

    def name(self) -> str:
        return "getBiome"

    def returnType(self) -> ResourceType:
        return ResourceType.NUMBER

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        if parameters:
            raise McScriptArgumentsError("Function getBiome expected no arguments.")

        commands = [Command.EXECUTE(
            sub=ExecuteCommand.IF_PREDICATE(predicate=predicate),
            command=Command.SET_VALUE(
                stack=compileState.config.RETURN_SCORE,
                value=index
            )
        ) for index, predicate in enumerate(self.predicates)]
        return multiple_commands(
            Command.SET_VALUE(stack=compileState.config.RETURN_SCORE, value=-1),
            *commands
        )

    def include(self, compileState: CompileState) -> Any:
        self.predicates = compileState.datapack.getUtilsDirectory().addBiomePredicate()

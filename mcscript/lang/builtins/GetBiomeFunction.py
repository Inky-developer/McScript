from __future__ import annotations

from typing import Any, TYPE_CHECKING

from mcscript.lang.builtins.builtins import CachedFunction
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class GetBiomeFunction(CachedFunction):
    """
    returns the biome id of the current biome the executor is in.
    """

    def __init__(self):
        super().__init__()
        self.predicates = None

    def name(self) -> str:
        return "getBiome"

    def returnType(self) -> ResourceType:
        return ResourceType.INTEGER

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
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

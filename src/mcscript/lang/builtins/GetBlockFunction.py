from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import Command, ExecuteCommand
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.Resource.StringResource import StringResource
from src.mcscript.lang.builtins.builtins import BuiltinFunction

if TYPE_CHECKING:
    from src.mcscript import CompileState


class GetBlockFunction(BuiltinFunction):
    """
    parameter => [Optional] x: Number the relative x coordinate
    parameter => [Optional] y: Number the relative y coordinate
    parameter => [Optional] z: Number the relative z coordinate
    returns an id for the current block (block at ~ ~ ~ relative to the executor)
    """

    def name(self) -> str:
        return "getBlock"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def include(self, compileState: CompileState):
        compileState.datapack.getUtilsDirectory().addGetBlockFunction()

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        # accept either no arguments or three numbers
        x = y = z = "~"
        if parameters and len(parameters) != 3:
            raise McScriptArgumentsError("Invalid number of arguments: expected <None> or <x, y, z>.")
        if not all(isinstance(resource, (NumberResource, StringResource)) for resource in parameters):
            raise McScriptArgumentsError("Invalid arguments: must be all of type Number or String")
        if parameters:
            x, y, z = [f"~{resource.value if resource.value != 0 else ''}" for resource in parameters]

        return Command.EXECUTE(
            sub=ExecuteCommand.POSITIONED(
                x=x,
                y=y,
                z=z
            ),
            command=Command.RUN_FUNCTION(
                name=compileState.config.UTILS,
                function="get_block.0"
            )
        )

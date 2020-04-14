from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import Command, ExecuteCommand
from mcscript.lang.builtins.builtins import BuiltinFunction
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class GetBlockFunction(BuiltinFunction):
    """
    parameter => [Optional=0] [Static] x: Number the relative x coordinate
    parameter => [Optional=0] [Static] y: Number the relative y coordinate
    parameter => [Optional=0] [Static] z: Number the relative z coordinate
    returns an id for the current block (block at ~ ~ ~ relative to the executor)
    """

    def name(self) -> str:
        return "getBlock"

    def returnType(self) -> ResourceType:
        return ResourceType.NUMBER

    def include(self, compileState: CompileState):
        compileState.datapack.getUtilsDirectory().addGetBlockFunction()

    # noinspection PyUnresolvedReferences
    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
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

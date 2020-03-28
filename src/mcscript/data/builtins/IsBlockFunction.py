from __future__ import annotations

from typing import TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import multiple_commands, Command, ExecuteCommand
from src.mcscript.data.builtins.builtins import BuiltinFunction
from src.mcscript.data.minecraftData.blocks import Blocks
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class IsBlockFunction(BuiltinFunction):
    """
    parameter => block: Number the block id
    parameter => [Optional] x: Number a relative x coordinate
    parameter => [Optional] y: Number a relative y coordinate
    parameter => [Optional] <z: Number a relative z coordinate
    Tests for a specific block.
    Returns true if the block matches.
    ToDO: allow isBlock(block.dirt) and get the location from current context

    Example:
        isBlock(block.dirt, 115, 128, 12)
    """

    def name(self) -> str:
        return "isBlock"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        """
        ToDO: Create System for managing relative and absolute coordinates (1, ~1, ^1)
        """
        x = y = z = "~"
        block, *rest = parameters
        if rest:
            # use current coordinates
            x, y, z = ["~" + str(i) if int(str(i)) != 0 else "~" for i in rest]
        if block.type() != ResourceType.NUMBER:
            raise McScriptArgumentsError("All arguments must be static for function 'isBlock'")

        return multiple_commands(
            Command.SET_VALUE(
                stack=compileState.config.RETURN_SCORE,
                value=0
            ),
            Command.EXECUTE(
                sub=ExecuteCommand.IF_BLOCK(
                    x=x,
                    y=y,
                    z=z,
                    block=Blocks.getBlockstateIndexed(block.value).block.minecraft_id
                ),
                command=Command.SET_VALUE(
                    stack=compileState.config.RETURN_SCORE,
                    value=1
                )
            ))

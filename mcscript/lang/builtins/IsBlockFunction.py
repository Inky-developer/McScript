from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import Command, ExecuteCommand, multiple_commands
from mcscript.data.minecraftData import blocks
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class IsBlockFunction(BuiltinFunction):
    """
    parameter => [Static] block: Number the block id
    parameter => [Optional=0] [Static] x: Number a relative x coordinate
    parameter => [Optional=0] [Static] y: Number a relative y coordinate
    parameter => [Optional=0] [Static] z: Number a relative z coordinate
    Tests for a specific block.
    Returns true if the block matches.

    Example:
        isBlock(block.dirt, 115, 128, 12)
    """

    def name(self) -> str:
        return "isBlock"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        block, *rest = parameters
        x, y, z = ["~" + str(i) if int(str(i)) != 0 else "~" for i in rest]

        stack = compileState.expressionStack.next()
        # noinspection PyUnresolvedReferences
        return FunctionResult(
            multiple_commands(
                Command.SET_VALUE(
                    stack=stack,
                    value=0
                ),
                Command.EXECUTE(
                    sub=ExecuteCommand.IF_BLOCK(
                        x=x,
                        y=y,
                        z=z,
                        block=blocks.getBlockstateIndexed(block.value).block.minecraft_id
                    ),
                    command=Command.SET_VALUE(
                        stack=stack,
                        value=1
                    )
                )), BooleanResource(stack, False)
        )

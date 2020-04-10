from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptArgumentsError
from mcscript.data.commands import multiple_commands, Command, ExecuteCommand
from mcscript.data.minecraftData.blocks import Blocks
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class IsBlockFunction(BuiltinFunction):
    """
    parameter => block: Number the block id
    parameter => [Optional] x: Number a relative x coordinate
    parameter => [Optional] y: Number a relative y coordinate
    parameter => [Optional] <z: Number a relative z coordinate
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

        stack = compileState.expressionStack.next()
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
                        block=Blocks.getBlockstateIndexed(block.value).block.minecraft_id
                    ),
                    command=Command.SET_VALUE(
                        stack=stack,
                        value=1
                    )
                )), BooleanResource(stack, False)
        )

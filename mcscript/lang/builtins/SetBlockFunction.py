from __future__ import annotations

from typing import TYPE_CHECKING, Union

from mcscript.data.commands import Command, ExecuteCommand, multiple_commands
from mcscript.data.minecraftData.blocks import Blocks
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class SetBlockFunction(BuiltinFunction):
    """
    parameter => block: Number the block to place
    parameter => [Optional=0] [static] x: Number the relative x coordinate
    parameter => [Optional=0] [Static] y: Number the relative y coordinate
    parameter => [Optional=0] [Static] z: Number the relative z coordinate
    """

    def __init__(self):
        super().__init__()
        self.shouldGenerate = False

    def name(self) -> str:
        return "setBlock"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def include(self, compileState: CompileState):
        if self.shouldGenerate:
            compileState.datapack.getUtilsDirectory().addSetBlockFunction()
        return False

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        block, *pos = parameters
        x, y, z = [f"~{i if float(str(i)) != 0 else ''}" for i in pos]

        if isinstance(block, ValueResource) and block.hasStaticValue:
            return self.generate_static(compileState, block.toNumber(), x, y, z)
        self.shouldGenerate = True
        return self.generate_dynamic(compileState, block.load(compileState), x, y, z)

    def generate_dynamic(self, compileState: CompileState, block: Resource, x: str, y: str, z: str) -> FunctionResult:
        stack = compileState.expressionStack.next()
        return FunctionResult(
            multiple_commands(
                Command.SET_VALUE_EQUAL(
                    stack=compileState.config.BLOCK_SCORE,
                    stack2=block
                ),
                Command.EXECUTE(
                    sub=ExecuteCommand.POSITIONED(
                        x=x,
                        y=y,
                        z=z
                    ),
                    command=Command.RUN_FUNCTION(
                        name=compileState.config.UTILS,
                        function="set_block.0"
                    )
                ),
                Command.SET_VALUE_FROM(
                    stack=stack,
                    command=Command.GET_SCOREBOARD_VALUE(stack=compileState.config.RETURN_SCORE)
                )
            ), BooleanResource(stack, False)
        )

    def generate_static(self, compileState: CompileState, block: int, x: str, y: str, z: str) -> FunctionResult:
        stack = compileState.expressionStack.next()
        return FunctionResult(
            multiple_commands(
                Command.SET_VALUE_FROM(
                    stack=stack,
                    command=Command.SET_BLOCK(
                        x=x,
                        y=y,
                        z=z,
                        block=Blocks.getBlockstateIndexed(block).getMinecraftName()
                    )
                )
            ), BooleanResource(stack, False)
        )

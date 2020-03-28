from __future__ import annotations

from typing import Union, TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import multiple_commands, Command, ExecuteCommand
from src.mcscript.data.Config import Config
from src.mcscript.data.builtins.builtins import BuiltinFunction, FunctionResult
from src.mcscript.data.minecraftData.blocks import Blocks
from src.mcscript.lang.Resource.NumberResource import NumberResource
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType
from src.mcscript.lang.Resource.StringResource import StringResource

if TYPE_CHECKING:
    from src.mcscript import CompileState


class SetBlockFunction(BuiltinFunction):
    """
    parameter => block: Number the block to place
    parameter => [Optional] x: Number the relative x coordinate
    parameter => [Optional] y: Number the relative y coordinate
    parameter => [Optional] z: Number the relative z coordinate
    """

    def __init__(self):
        super().__init__()
        self.shouldGenerate = False

    def name(self) -> str:
        return "setBlock"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def include(self, compileState: CompileState):
        # ToDo: only do this when generate_dynamic is used
        if self.shouldGenerate:
            compileState.datapack.getUtilsDirectory().addSetBlockFunction()
        return False

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        if len(parameters) not in (1, 4):
            raise McScriptArgumentsError("Invalid number of arguments: expected <block> or <block, x, y, z>.")
        x = y = z = "~"
        block, *rest = parameters
        if rest:
            if not all(isinstance(i, (NumberResource, StringResource)) for i in rest):
                raise McScriptArgumentsError("Arguments <x, y, z> must be static and of type Number or String")
            x, y, z = [f"~{i if float(str(i)) != 0 else ''}" for i in rest]

        if isinstance(block, ValueResource) and block.hasStaticValue:
            try:
                return self.generate_static(compileState.config, block.toNumber(), x, y, z)
            except TypeError:
                pass
        self.shouldGenerate = True
        return self.generate_dynamic(compileState.config, block.load(compileState), x, y, z)

    def generate_dynamic(self, config: Config, block: Resource, x: str, y: str, z: str) -> str:
        return multiple_commands(
            Command.SET_VALUE_EQUAL(
                stack=config.BLOCK_SCORE,
                stack2=block
            ),
            Command.EXECUTE(
                sub=ExecuteCommand.POSITIONED(
                    x=x,
                    y=y,
                    z=z
                ),
                command=Command.RUN_FUNCTION(
                    name=config.UTILS,
                    function="set_block.0"
                )
            )
        )

    def generate_static(self, config: Config, block: int, x: str, y: str, z: str) -> str:
        return multiple_commands(
            Command.SET_VALUE_FROM(
                stack=config.RETURN_SCORE,
                command=Command.SET_BLOCK(
                    x=x,
                    y=y,
                    z=z,
                    block=Blocks.getBlockstateIndexed(block).getMinecraftName()
                )
            )
        )

from __future__ import annotations

from typing import List, TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import multiple_commands, Command, ExecuteCommand, Selector
from src.mcscript.data.builtins.builtins import CachedFunction
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class RandomFunction(CachedFunction):
    """ generates a random value between """

    def name(self) -> str:
        return "random"

    def returnType(self) -> ResourceType:
        return ResourceType.NUMBER

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        if len(parameters) > 1:
            raise McScriptArgumentsError("Invalid number of arguments: Expected <[bits]>")
        # noinspection PyTypeChecker
        bits = int(parameters[0]) if parameters else 31
        if 0 >= bits > 31:
            raise McScriptArgumentsError("Invalid value for parameter <bits>: Must be 1 <= <bits> <= 31")
        statements: List[str] = []

        # ToDo: make sure that tags are unique
        tag = f"{compileState.config.NAME}_randomizer"
        stack = compileState.config.RETURN_SCORE
        statements.append(
            multiple_commands(
                Command.SUMMON_ENTITY(entity="minecraft:area_effect_cloud",
                                      nbt={"Tags": [tag, f"{tag}_0"]}),
                Command.SUMMON_ENTITY(entity="minecraft:area_effect_cloud",
                                      nbt={"Tags": [tag, f"{tag}_1"]}),
                Command.SET_VALUE(
                    stack=stack,
                    value=0
                )
            )
        )

        for i in range(bits):
            statements.append(Command.EXECUTE(
                sub=ExecuteCommand.AS(
                    target=Selector.ALL_ENTITIES.filter(tag=tag, sort="random", limit=1),
                    command=ExecuteCommand.IF_ENTITY(target=Selector.CURRENT_ENTITY.filter(tag=f"{tag}_1"))
                ),
                command=Command.ADD(
                    target=stack,
                    value=2 ** i
                )
            ))

        # not necessary, area effect cloud will be killed automatically by minecraft
        # statements.append(
        #     Command.KILL_ENTITY(target=Selector.ALL_ENTITIES.filter(tag=tag))
        # )

        return multiple_commands(*statements)

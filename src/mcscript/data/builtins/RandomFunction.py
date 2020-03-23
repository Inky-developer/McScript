from __future__ import annotations

from typing import List, TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import multiple_commands, Command, ExecuteCommand
from src.mcscript.data.builtins.builtins import CachedFunction
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class RandomFunction(CachedFunction):
    """ generates a random value between 0 and 2**bits - 1"""

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

        stack = compileState.config.RETURN_SCORE

        for i in range(bits):
            statements.append(Command.EXECUTE(
                sub=ExecuteCommand.IF_PREDICATE(predicate=self.predicate),
                command=Command.ADD_SCORE(
                    stack=stack,
                    value=2 ** i
                )
            ))

        return multiple_commands(
            Command.SET_VALUE(stack=stack, value=0),
            *statements
        )

    def include(self, compileState: CompileState):
        self.predicate, = compileState.datapack.getUtilsDirectory().addRandomPredicate()

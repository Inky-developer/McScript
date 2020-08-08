from __future__ import annotations

from typing import List, TYPE_CHECKING

from mcscript.exceptions.compileExceptions import McScriptArgumentsError
from mcscript.lang.builtins.builtins import CachedFunction
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class RandomFunction(CachedFunction):
    """
    parameter => [Optional=31] [Static] bits: Number
    generates a random value between 0 and 2**bits - 1
    """

    def __init__(self):
        super().__init__()
        self.predicate = None

    def name(self) -> str:
        return "random"

    def returnType(self) -> ResourceType:
        return ResourceType.INTEGER

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        # noinspection PyTypeChecker
        bits = int(parameters[0])
        if not 0 <= bits < 32:
            raise McScriptArgumentsError("Invalid value for parameter <bits>: Must be 0 <= <bits> <= 31", compileState)
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

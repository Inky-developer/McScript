from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.predicates.RandomChancePredicate import RandomChancePredicate
from mcscript.exceptions.compileExceptions import McScriptArgumentsError
from mcscript.lang.builtins.builtins import CachedFunction
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class RandomChanceFunction(CachedFunction):
    """
    parameter => [Optional=0.5] [Static] chance: Fixed the chance that this function returns true

    Unlike the random function which generates a random value between 0 and 2**bits-1,
    this function takes a chance as an input and returns a boolean based on this chance.
    if no parameter is given the chance will be 50%.

    Example:
        randomChance(1.0)
        -> true

        randomChance(0.0)
        -> false

        randomChance(0.25)
        -> 0.25 chance of being true

        randomChance()
        -> 50% chance of being true
    """

    def name(self) -> str:
        return "randomChance"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> str:
        parameter: FixedNumberResource
        parameter, = parameters

        number = parameter.static_value / parameter.BASE

        if 1 < number or 0 > number:
            raise McScriptArgumentsError(f"parameter chance must be between 0 and 1, got {number}", compileState)

        # generate the predicate
        filestructure = compileState.datapack.getUtilsDirectory().getPath("predicates").files
        predicate, = RandomChancePredicate(number).generate(filestructure)

        # execute if the predicate succeeds
        stack = compileState.config.RETURN_SCORE
        return multiple_commands(
            Command.SET_VALUE(
                stack=stack,
                value=0
            ),
            Command.EXECUTE(
                sub=ExecuteCommand.IF_PREDICATE(predicate=predicate),
                command=Command.SET_VALUE(stack=stack, value=1)
            )
        )

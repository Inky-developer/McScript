from __future__ import annotations

from typing import Union, TYPE_CHECKING

from src.mcscript.Exceptions import McScriptArgumentsError, McScriptTypeError
from src.mcscript.data.Commands import Command, ExecuteCommand, multiple_commands
from src.mcscript.data.builtins.builtins import CachedFunction, FunctionResult
from src.mcscript.data.predicates.RandomChancePredicate import RandomChancePredicate
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class RandomChanceFunction(CachedFunction):
    """
    Unlike the random function which generates a random value between 0 and 2**bits-1,
    this function takes a chance as an input and returns a boolean based on this chance.
    if no parameter is given the chance will be 50%.
    Example:
        randomChance(1)
        -> true
        randomChance(0)
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

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        if len(parameters) > 1:
            raise McScriptArgumentsError(f"Function randomChance expected exactly one argument, got {len(parameters)}")

        if len(parameters) == 0:
            parameter = FixedNumberResource.fromNumber(0.5)
        else:
            parameter, = parameters

        try:
            if parameter.type() == ResourceType.STRING:
                number = float(parameter.embed())
            else:
                parameter = parameter.convertToFixedNumber(compileState)
                if not parameter.hasStaticValue:
                    raise McScriptArgumentsError("Function randomChance: parameter <chance> must be static!")
                number = parameter.value / parameter.BASE
        except TypeError:
            raise McScriptTypeError(
                f"Function randomChance: Could not convert parameter {repr(parameter)} to a fixed-point number"
            )

        # generate the predicate
        filestructure = compileState.datapack.getUtilsDirectory().getPath("predicates").fileStructure
        predicate, = RandomChancePredicate(number).generate(filestructure)

        # execute if the predicate succeeds
        return multiple_commands(
            Command.SET_VALUE(
                stack=compileState.config.RETURN_SCORE,
                value=0
            ),
            Command.EXECUTE(
                sub=ExecuteCommand.IF_PREDICATE(predicate=predicate),
                command=Command.SET_VALUE(stack=compileState.config.RETURN_SCORE, value=1)
            )
        )

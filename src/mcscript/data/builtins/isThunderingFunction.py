from __future__ import annotations

from typing import Union, TYPE_CHECKING, Any

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import multiple_commands, Command, ExecuteCommand
from src.mcscript.data.builtins.builtins import BuiltinFunction, FunctionResult
from src.mcscript.data.predicates.WeatherPredicate import WeatherPredicate
from src.mcscript.lang.Resource.ResourceBase import Resource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class IsThundering(BuiltinFunction):
    """
    returns whether it is currently thundering
    """

    def name(self) -> str:
        return "isThundering"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        if len(parameters) != 0:
            raise McScriptArgumentsError("Function isThundering expected no arguments.")
        return multiple_commands(
            Command.SET_VALUE(
                stack=compileState.config.RETURN_SCORE,
                value=0
            ),
            Command.EXECUTE(
                sub=ExecuteCommand.IF_PREDICATE(
                    predicate=self.thunderingPredicate
                ),
                command=Command.SET_VALUE(
                    stack=compileState.config.RETURN_SCORE,
                    value=1
                )
            )
        )

    def include(self, compileState: CompileState) -> Any:
        compileState.datapack.getUtilsDirectory().addWeatherPredicate()
        raining, thundering = WeatherPredicate().keys
        self.thunderingPredicate: str = thundering

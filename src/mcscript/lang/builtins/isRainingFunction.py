from __future__ import annotations

from typing import Union, TYPE_CHECKING, Any

from src.mcscript.Exceptions import McScriptArgumentsError
from src.mcscript.data.Commands import multiple_commands, Command, ExecuteCommand
from src.mcscript.data.predicates.WeatherPredicate import WeatherPredicate
from src.mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from src.mcscript.lang.resource.BooleanResource import BooleanResource
from src.mcscript.lang.resource.base.ResourceBase import Resource
from src.mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class IsRaining(BuiltinFunction):
    """
    returns whether it is currently raining
    """

    def name(self) -> str:
        return "isRaining"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
        if len(parameters) != 0:
            raise McScriptArgumentsError("Function isRaining expected no arguments.")

        stack = compileState.expressionStack.next()
        return FunctionResult(
            multiple_commands(
                Command.SET_VALUE(
                    stack=stack,
                    value=0
                ),
                Command.EXECUTE(
                    sub=ExecuteCommand.IF_PREDICATE(
                        predicate=self.rainingPredicate
                    ),
                    command=Command.SET_VALUE(
                        stack=stack,
                        value=1
                    )
                )
            ), BooleanResource(stack, False)
        )

    def include(self, compileState: CompileState) -> Any:
        compileState.datapack.getUtilsDirectory().addWeatherPredicate()
        raining, thundering = WeatherPredicate().keys
        self.rainingPredicate: str = raining

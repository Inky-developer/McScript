from __future__ import annotations

from typing import Any, TYPE_CHECKING, Union

from mcscript.data.predicates.WeatherPredicate import WeatherPredicate
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class IsRaining(BuiltinFunction):
    """
    returns whether it is currently raining
    """

    def __init__(self):
        super().__init__()
        self.rainingPredicate = None

    def name(self) -> str:
        return "isRaining"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> Union[str, FunctionResult]:
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

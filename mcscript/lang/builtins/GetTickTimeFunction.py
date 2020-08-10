from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.lang.resource.base.ResourceType import ResourceType

from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.IntegerResource import IntegerResource
from mcscript.lang.resource.base.ResourceBase import Resource

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class GetTickTimeFunction(BuiltinFunction):
    """
    Returns the amount of milliseconds that have passed since the start of this tick.
    Important: To get this data, this function has to manipulate the world border. If this function is used, do NOT
    modify the worldborder either manually or via another datapack!

    Notes:
        - Currently seems not to be reliable on servers. I have no clue why
    """

    def name(self) -> str:
        return "getTickTime"

    def returnType(self) -> ResourceType:
        return ResourceType.INTEGER

    def include(self, compileState: CompileState) -> bool:
        compileState.datapack.getMainDirectory().hasSubTickClock = True
        return True

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        stack = compileState.config.RETURN_SCORE
        const_border = compileState.getConstant(59_999_000)
        return FunctionResult(
            multiple_commands(
                Command.SET_VALUE_FROM(
                    stack=stack,
                    command="worldborder get"
                ),
                Command.OPERATION(
                    stack=stack,
                    operator=BinaryOperator.MINUS.value,
                    stack2=const_border
                ),
                # Command.OPERATION(
                #     stack=stack,
                #     operator=BinaryOperator.TIMES.value,
                #     stack2=compileState.getConstant(-1)
                # )
            ), IntegerResource(stack, False)
        )

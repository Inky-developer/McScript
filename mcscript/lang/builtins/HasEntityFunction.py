from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.commands import Command, ExecuteCommand, multiple_commands
from mcscript.lang.builtins.builtins import BuiltinFunction, FunctionResult
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.SelectorResource import SelectorResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class HasEntityFunction(BuiltinFunction):
    """
    parameter => entity: Selector the entities to test for

    Returns if the specified selector matches any entity.
    """

    def name(self) -> str:
        return "hasEntity"

    def returnType(self) -> ResourceType:
        return ResourceType.BOOLEAN

    def generate(self, compileState: CompileState, *parameters: Resource) -> FunctionResult:
        target: SelectorResource
        target, = parameters
        return FunctionResult(
            multiple_commands(
                Command.SET_VALUE(
                    stack=compileState.config.RETURN_SCORE,
                    value=0
                ),
                Command.EXECUTE(
                    sub=ExecuteCommand.IF_ENTITY(target=target.embed_non_static(compileState)),
                    command=Command.SET_VALUE(
                        stack=compileState.config.RETURN_SCORE,
                        value=1
                    )
                )
            ), BooleanResource(compileState.config.RETURN_SCORE, False)
        )

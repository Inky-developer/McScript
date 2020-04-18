from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.Exceptions.compileExceptions import McScriptNotStaticError
from mcscript.data.commands import Command, ExecuteCommand, Selector, Struct, multiple_commands
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.lang.ResourceTextFormatter import ResourceTextFormatter


class SelectorResource(ValueResource):
    """
    Holds a minecraft selector
    """

    def embed(self) -> str:
        return self.value

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.SELECTOR

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> SelectorResource:
        """
        creates a score for all entities that match this selector and stores this score numerically on a scoreboard.
        This is constant and that is why there is no load implementation

        Args:
            stack: the stack on the data storage
            compileState: the compile state

        Returns:
            A non-static SelectorResource
        """

        # first set the entities score to the entity id
        # store the entity id to a storage
        # increment the entity id

        stack = compileState.selectorStorageStack.next()
        # add the score to compile state
        compileState.selectorStack2Score[stack] = compileState.selectorStorageStack.value - 1

        compileState.writeline(multiple_commands(
            Command.EXECUTE(
                sub=ExecuteCommand.AS(target=self.embed()),
                command=Command.OPERATION(
                    stack=Selector.CURRENT_ENTITY(),
                    name=compileState.config.get_scoreboard("entities"),
                    stack2=compileState.config.get_score("entityId")
                )
            ),
            Command.SET_VARIABLE_FROM(
                var=stack,
                command=Command.GET_SCOREBOARD_VALUE(
                    stack=compileState.config.get_score("entityId")
                )
            ),
            Command.ADD_SCORE(
                stack=compileState.config.get_score("entityId"),
                value=1
            )
        ))

        return SelectorResource(stack, False)

    def toJsonString(self, compileState: CompileState, formatter: ResourceTextFormatter) -> str:
        if self.isStatic:
            raise TypeError
        value = compileState.selectorStack2Score.get(self.value, None)
        if value is None:
            raise McScriptNotStaticError(f"Failed to infer the static value of SelectorResource {self.value}.\n"
                                         f"Note: this resource can (at the moment) not be used in lists.", compileState)
        return formatter.createFromResources(SelectorResource(
            Selector.ALL_ENTITIES.filter(scores=Struct.fromDict({
                compileState.config.get_scoreboard("entities"): value
            })), True
        ))

from __future__ import annotations

from typing import TYPE_CHECKING

from lark import Tree

from mcscript.compiler.NamespaceType import NamespaceType
from mcscript.data.Scoreboard import Scoreboard
from mcscript.data.commands import Command, ExecuteCommand, Selector, Struct, multiple_commands
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
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

    def embed_non_static(self, compileState: CompileState) -> str:
        if self.isStatic:
            return self.embed()
        scoreboard, = filter(lambda x: x.name == "entities", compileState.scoreboards)
        return Selector.ALL_ENTITIES.filter(scores=Struct.fromDict({
            scoreboard.get_name(): self.value
        }))

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.SELECTOR

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> SelectorResource:
        """
        creates a score for all entities that match this selector and stores this score numerically on a scoreboard.
        This is constant and that is why there is no load implementation

        Notes:
            In this implementation it is actually not necessary to store anything as nbt.
            Additionally, I think that this implementation is too dirty and I will change it later (ToDo)
            This includes the fact that in a non-static loop weird things can happen

        Args:
            stack: the stack on the data storage
            compileState: the compile state

        Returns:
            A non-static SelectorResource
        """

        value = compileState.selectorCounter
        compileState.selectorCounter += 1
        scoreboard, = filter(lambda x: x.name == "entities", compileState.scoreboards)

        compileState.writeline(multiple_commands(
            Command.EXECUTE(
                sub=ExecuteCommand.AS(target=self.embed()),
                command=Command.SET_VALUE(
                    stack=Selector.CURRENT_ENTITY(),
                    name=scoreboard.get_name(),
                    value=value
                )
            )
        ))

        return SelectorResource(value, False)

    def operation_get_element(self, compileState: CompileState, index: Resource) -> NumberResource:
        string = index.toString()
        ids = list(filter(lambda x: x.name == string, compileState.scoreboards))
        if not ids:
            scoreboard = Scoreboard(string, False, len(compileState.scoreboards))
            compileState.scoreboards.append(scoreboard)
        else:
            scoreboard, = ids

        stack = compileState.expressionStack.next()
        # ToDO: this fails if the selector can possibly find more than one entity
        # Todo: more efficient lookup
        compileState.writeline(Command.SET_VALUE_EQUAL(
            stack=stack,
            stack2=self.value,
            name2=scoreboard.get_name()
        ))
        return NumberResource(stack, False)

    def operation_set_element(self, compileState: CompileState, index: Resource, value: Resource):
        string = index.toString()
        ids = list(filter(lambda x: x.name == string, compileState.scoreboards))
        if not ids:
            scoreboard = Scoreboard(string, False, len(compileState.scoreboards))
            compileState.scoreboards.append(scoreboard)
        else:
            scoreboard, = ids
        value = value.convertToNumber(compileState)

        if value.isStatic:
            compileState.writeline(Command.SET_VALUE(
                stack=self.value,
                name=scoreboard.get_name(),
                value=value.value
            ))
        else:
            compileState.writeline(Command.SET_VALUE_EQUAL(
                stack=self.value,
                name=scoreboard.get_name(),
                stack2=value.value
            ))

    def iterate(self, compileState: CompileState, varName: str, tree: Tree):
        """ identical to `run for @. at @s` """

        block = compileState.pushBlock(namespaceType=NamespaceType.LOOP)
        compileState.currentNamespace()[varName] = SelectorResource(Selector.CURRENT_ENTITY(), True)
        for child in tree.children:
            compileState.compileFunction(child)
        compileState.popBlock()

        compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.AS(
                target=self.embed_non_static(compileState),
                command=ExecuteCommand.AT(
                    target=Selector.CURRENT_ENTITY()
                )
            ),
            command=Command.RUN_FUNCTION(function=block)
        ))

    def toJsonString(self, compileState: CompileState, formatter: ResourceTextFormatter) -> str:
        if self.isStatic:
            raise TypeError
        return formatter.createFromResources(SelectorResource(
            self.embed_non_static(compileState), True
        ))

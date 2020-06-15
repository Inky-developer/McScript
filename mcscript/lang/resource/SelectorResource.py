from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from lark import Tree

from mcscript.compiler.ContextType import ContextType
from mcscript.data.commands import Command, ExecuteCommand, multiple_commands, Selector as CmdSelector, Struct
from mcscript.data.Scoreboard import Scoreboard
from mcscript.data.selector.Selector import Selector
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.StringResource import StringResource

if TYPE_CHECKING:
    from mcscript.compiler.Context import Context
    from mcscript.compiler.CompileState import CompileState
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter


class SelectorResource(ValueResource):
    """
    Holds a minecraft selector
    """

    def __init__(self, value: str, isStatic: bool, compileState: CompileState = None, context: Context = None):
        if isStatic:
            if context:
                namespace_dict = context.as_dict()
                replacements = {key: namespace_dict[key].resource for key in namespace_dict}
                value = StringResource.StringFormatter().format(value, **replacements)

            value = Selector.from_string(value, compileState)

            # if this resource is created from user code and a compile state is available, verify that this is valid
            if compileState is not None:
                value.verify(compileState)
                value.sort()
        super().__init__(value, isStatic)

    def embed(self) -> str:
        return str(self.value)

    def embed_non_static(self, compileState: CompileState) -> str:
        if self.isStatic:
            return self.embed()
        scoreboard, = filter(lambda x: x.name == "entities", compileState.scoreboards)
        return CmdSelector.ALL_ENTITIES.filter(scores=Struct.fromDict({
            scoreboard.get_name(): self.value
        }))

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.SELECTOR

    def typeCheck(self) -> bool:
        return isinstance(self.value, Selector)

    def storeToNbt(self, _: Optional[NbtAddressResource], compileState: CompileState) -> SelectorResource:
        """
        creates a score for all entities that match this selector and stores this score numerically on a scoreboard.
        This is constant and that is why there is no load implementation

        Notes:
            In this implementation it is actually not necessary to store anything as nbt.
            Additionally, I think that this implementation is too dirty and I will change it later (ToDo)
            Optimize the scoreboard players set 0 thing if it is not necessary

        Args:
            _: the stack on the data storage
            compileState: the compile state

        Returns:
            A non-static SelectorResource
        """

        value = compileState.selectorCounter
        compileState.selectorCounter += 1
        scoreboard, = filter(lambda x: x.name == "entities", compileState.scoreboards)

        compileState.writeline(multiple_commands(
            Command.SET_VALUE(
                stack=CmdSelector.ALL_ENTITIES(),
                name=scoreboard.get_name(),
                value=0
            ),
            Command.EXECUTE(
                sub=ExecuteCommand.AS(target=self.embed()),
                command=Command.SET_VALUE(
                    stack=CmdSelector.CURRENT_ENTITY(),
                    name=scoreboard.get_name(),
                    value=value
                )
            )
        ))

        return SelectorResource(value, False, compileState)

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
            stack2=self.embed_non_static(compileState),
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
                stack=self.embed_non_static(compileState),
                name=scoreboard.get_name(),
                value=value.value
            ))
        else:
            compileState.writeline(Command.SET_VALUE_EQUAL(
                stack=self.embed_non_static(compileState),
                name=scoreboard.get_name(),
                stack2=value.value
            ))

    def iterate(self, compileState: CompileState, varName: str, tree: Tree):
        """ identical to `run for @. at @s` """

        block = compileState.pushBlock(ContextType.LOOP, tree.line, tree.column)
        compileState.currentContext().add_var(
            varName,
            SelectorResource(CmdSelector.CURRENT_ENTITY(), True, compileState).storeToNbt(None, compileState)
        )

        for child in tree.children:
            compileState.compileFunction(child)
        compileState.popBlock()

        compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.AS(
                target=self.embed_non_static(compileState),
                command=ExecuteCommand.AT(
                    target=CmdSelector.CURRENT_ENTITY()
                )
            ),
            command=Command.RUN_FUNCTION(function=block)
        ))

    def toTextJson(self, compileState: CompileState, formatter: ResourceTextFormatter) -> list:
        return formatter.handlers[self.type()](
            self.embed_non_static(compileState)
        )

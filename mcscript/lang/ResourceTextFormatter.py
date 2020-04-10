from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from mcscript.data import getDictionaryResource
from mcscript.data.commands import Command, stringFormat, Type
from mcscript.lang.resource.FixedNumberResource import FixedNumberResource
from mcscript.lang.resource.FixedNumberVariableResource import FixedNumberVariableResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class PrintCommand(Enum):
    TELLRAW = Command.TELLRAW
    TITLE = Command.TITLE
    SUBTITLE = Command.SUBTITLE
    ACTIONBAR = Command.ACTIONBAR


class ResourceTextFormatter:
    handler = getDictionaryResource("TextFormatter.txt")

    def __init__(self, compileState: CompileState):
        self.compileState = compileState

    def createCommandFromResources(self, command: PrintCommand, *resources: Resource) -> str:
        return self.createCommand(command, self.createFromResources(*resources))

    @staticmethod
    def createCommand(command: PrintCommand, text: str) -> str:
        return command.value(text=text)

    def createFromResources(self, *resources: Resource) -> str:
        handlers = {
            ResourceType.ADDRESS: "Score",
            ResourceType.NBT_ADDRESS: "NBT",
            ResourceType.SELECTOR: "Selector",
            None: "Default"
        }

        data = ['""']
        for resource in resources:
            fName = f"on_{resource.type().name}"
            if hasattr(self, fName):
                resource = getattr(self, fName)(resource)
            handler = handlers.get(resource.type(), None)
            if handler is None:
                try:
                    handler = handlers.get(resource.value.type() if isinstance(resource.value,
                                                                               Resource) else None, None)
                except AttributeError:
                    # the resource might not be a value resource
                    handler = handlers[None]

            stringValue = resource.embed() if isinstance(resource, ValueResource) else repr(resource)
            data.append(self._getFormattedString(handler, stringValue))

        return f'[{",".join(data)}]'

    def _getFormattedString(self, rawString, resource):
        return stringFormat(self.handler.get(rawString), value=resource)

    def on_FIXED_POINT(self, resource: FixedNumberResource) -> Resource:
        """
        loadToScoreboard the number to a scoreboard as a float an refer to it as the value
        """
        if resource.isStatic:
            return resource

        stack = self.compileState.temporaryStorageStack.next()

        if isinstance(resource, FixedNumberResource):
            self.compileState.writeline(Command.SET_VARIABLE_FROM(
                var=stack,
                scale=f"{1 / FixedNumberResource.BASE:.16f}",
                type=Type.FLOAT,
                command=Command.GET_SCOREBOARD_VALUE(stack=resource.value)
            ))
        elif isinstance(resource, FixedNumberVariableResource):
            return resource.value
        else:
            raise ValueError("Unknown Resource type for fixed number resources")

        return NbtAddressResource(str(stack))

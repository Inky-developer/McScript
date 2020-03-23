from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from src.mcscript.data import getDictionaryResource
from src.mcscript.data.Commands import Command, stringFormat, Type
from src.mcscript.lang.Resource.FixedNumberResource import FixedNumberResource
from src.mcscript.lang.Resource.NbtAddressResource import NbtAddressResource
from src.mcscript.lang.Resource.ResourceBase import Resource, ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    from src.mcscript import CompileState


class PrintCommand(Enum):
    TELLRAW = Command.TELLRAW
    TITLE = Command.TITLE
    SUBTITLE = Command.SUBTITLE
    ACTIONBAR = Command.ACTIONBAR


class TextFormatter:
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
        text = '["",{}]'

        data = []
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

        return text.format(",".join(data))

    def _getFormattedString(self, rawString, resource):
        return stringFormat(self.handler.get(rawString), value=resource)

    def on_FIXED_POINT(self, resource: FixedNumberResource) -> Resource:
        """
        loadToScoreboard the number to a scoreboard as a float an refer to it as the value
        """
        if resource.isStatic:
            return resource
        stack = self.compileState.temporaryStorageStack.next()
        self.compileState.writeline(Command.SET_VARIABLE_FROM(
            var=stack,
            scale=f"{1 / FixedNumberResource.BASE:.16f}",
            type=Type.FLOAT,
            command=Command.GET_SCOREBOARD_VALUE(stack=resource.value)
        ))
        return NbtAddressResource(str(stack))

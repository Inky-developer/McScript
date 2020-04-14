from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Union

from mcscript.data import getDictionaryResource
from mcscript.data.commands import Command, stringFormat
from mcscript.lang.resource.StringResource import StringResource
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
    handlers = {
        ResourceType.ADDRESS    : "Score",
        ResourceType.NBT_ADDRESS: "NBT",
        ResourceType.SELECTOR   : "Selector",
        None                    : "Default"
    }
    handler = getDictionaryResource("TextFormatter.txt")

    def __init__(self, compileState: CompileState):
        self.compileState = compileState

    def createCommandFromResources(self, command: PrintCommand, *resources: Resource) -> str:
        return self.createCommand(command, f"[{self.createFromResources(*resources)}]")

    @staticmethod
    def createCommand(command: PrintCommand, text: str) -> str:
        return command.value(text=text)

    def createFromResources(self, *resources: Union[str, Resource]) -> str:
        data = []
        for resource in resources:
            if isinstance(resource, str):
                resource = StringResource(resource, True)
            handler = self.handlers.get(resource.type(), None)
            if handler is None:
                if isinstance(resource, ValueResource):
                    handler = self.handlers.get(resource.value.type() if isinstance(resource.value,
                                                                                    Resource) else None, None)
                else:
                    # the resource might not be a value resource
                    handler = self.handlers[None]

            try:
                stringValue = resource.toJsonString(self.compileState, self)
                data.append(stringValue)
            except TypeError:
                stringValue = str(resource)
                data.append(self._getFormattedString(handler, stringValue))

        return ",".join(data)

    def _getFormattedString(self, rawString, resource):
        return stringFormat(self.handler.get(rawString), value=resource)

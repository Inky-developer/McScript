from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING, Union

from mcscript.data import Config
from mcscript.data.commands import Storage
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.JsonTextFormat.objectFormatter import format_nbt, format_score, format_selector, format_text

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class ResourceTextFormatter:
    handlers = {
        ResourceType.ADDRESS    : lambda r: format_score(Config.currentConfig.NAME, str(r)),
        ResourceType.NBT_ADDRESS: lambda r: format_nbt(f"{Config.currentConfig.NAME}:{Storage.NAME}", str(r)),
        ResourceType.SELECTOR   : lambda r: format_selector(str(r)),
        None                    : lambda r: format_text(str(r))
    }

    def __init__(self, compileState: CompileState):
        self.compileState = compileState

    def createFromResources(self, *resources: Union[str, Resource]) -> List:
        data = []
        for resource in resources:
            data.append(self.createFromResource(resource))

        return data

    def createFromResource(self, resource: Union[Resource, str]) -> Dict:
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
            return resource.toTextJson(self.compileState, self)
        except TypeError:
            value = str(resource)
            return self._getFormattedString(handler, value)

    def _getFormattedString(self, handler, resource) -> Dict:
        return handler(resource)

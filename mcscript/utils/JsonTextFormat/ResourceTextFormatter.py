from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING, Union

from mcscript.data import Config
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.JsonTextFormat.objectFormatter import format_nbt, format_score, format_selector, format_text

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class ResourceTextFormatter:
    def __init__(self, compileState: CompileState):
        self.compileState = compileState

    def createFromResources(self, *resources: Union[str, Resource]) -> List:
        data = []
        for resource in resources:
            data.append(self.createFromResource(resource))

        return data

    def createFromResource(self, resource: Union[Resource, str]) -> Dict:
        if isinstance(resource, str):
            resource = StringResource(resource)

        try:
            return resource.toTextJson(self.compileState, self)
        except TypeError:
            raise ValueError(f"Cannot use resource {resource} as a json string")

    def _getFormattedString(self, handler, resource) -> Dict:
        return handler(resource)

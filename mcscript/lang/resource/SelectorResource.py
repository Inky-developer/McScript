from __future__ import annotations

from typing import TYPE_CHECKING

from mcscript.data.selector.Selector import Selector
from mcscript.lang import atomic_types
from mcscript.lang.Type import Type
from mcscript.lang.resource.StringResource import StringResource
from mcscript.lang.resource.base.ResourceBase import Resource
from mcscript.utils.JsonTextFormat.objectFormatter import format_selector

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter


class SelectorResource(Resource):
    """
    Holds a minecraft selector
    """

    def __init__(self, value: str, compileState: CompileState = None):
        super().__init__()
        if compileState is not None:
            namespace_dict = compileState.currentContext().as_dict()
            replacements = {key: str(namespace_dict[key].resource) for key in namespace_dict}

            value = Selector.from_string(StringResource.StringFormatter().format(value, **replacements), compileState)

            value.verify(compileState)
            value.sort()
        else:
            value = Selector.from_string(value)

        self.value: Selector = value

    def type(self) -> Type:
        return atomic_types.Selector

    def supports_scoreboard(self) -> bool:
        return False

    def supports_storage(self) -> bool:
        return False

    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> dict:
        return format_selector(str(self.value))

from __future__ import annotations

from typing import List, TYPE_CHECKING

from mcscript.exceptions.compileExceptions import (
    McScriptTypeError, McScriptArgumentsError,
)
from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import Tuple
from mcscript.lang.resource.base.ResourceBase import Resource

if TYPE_CHECKING:
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.compiler.CompileState import CompileState


class TupleResource(Resource):
    """
    A tuple. Has a fixed size and can thus manage its elements without an nbt array.
    pointers to the resources are kept internally and can be accessed via static element access or for loops.
    This makes this class really lightweight when compiling to mcfunction files, but has some limitations.
    Namely, after the array was created, only read-access is possible in a non-static context after
    the initialization context.
    If this is a problem, the more dynamic and heavy List resource should be used:

    See Also:
        :class:`mcscript.lang.resource.ListResource.ListResource`
        :class:`mcscript.lang.resource.base.ResourceBase.Resource`
    """

    def __init__(self, *resources: Resource):
        super().__init__()

        self.resources = list(resources)

    def type(self) -> Type:
        return Tuple

    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> List:
        resources: list = [self.resources[0]] if self.resources else []
        for resource in self.resources[1:]:
            resources.append(", ")
            resources.append(resource)
        return formatter.createFromResources("(", *resources, ")")

    def operation_get_element(self, compileState: CompileState, index: Resource) -> Resource:
        try:
            value = index.integer_value()
        except TypeError:
            raise McScriptTypeError(f"Cannot convert {index} into a static integer", compileState)

        try:
            return self.resources[value]
        except ValueError:
            raise McScriptArgumentsError(f"Tuple index out of bounds. Maximum index is {len(self.resources) - 1}",
                                         compileState)

    def size(self) -> int:
        return len(self.resources)

    def __str__(self):
        return f"Tuple({', '.join(str(i) for i in self.resources)})"

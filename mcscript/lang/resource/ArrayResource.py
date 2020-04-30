from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from lark import Tree

from mcscript.Exceptions.compileExceptions import McScriptAttributeError, McScriptIndexError, McScriptTypeError
from mcscript.compiler.NamespaceType import NamespaceType
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NullResource import NullResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import MinecraftDataStorage, Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.compiler.CompileState import CompileState


class ArrayResource(Resource):
    """
    An Array. Has a fixed size and can thus manage it's elements without an nbt array.
    pointers to the resources are kept internally and can be accesses via static element access or for loops.
    This makes this class really lightweight when compiling to mcfunction files, but has some major limitations.
    Namely, after the array was created, only read-access is possible.
    If this is a problem, the more dynamic and heavy List resource should be used:

    See Also:
        :class:`mcscript.lang.resource.ListResource.ListResource`
        :class:`mcscript.lang.resource.base.ResourceBase.Resource`
    """

    def __init__(self, *resources: Resource):
        super().__init__()

        self.resources = list(resources)
        self.stack: Optional[NbtAddressResource] = None

        self.attributes = dict(size=NumberResource(len(self.resources), True))

    @staticmethod
    def type() -> ResourceType:
        return ResourceType.ARRAY

    def allow_redefine(self, compileState) -> bool:
        return compileState.currentNamespace().isContextStatic()

    def iterate(self, compileState: CompileState, varName: str, block: Tree):
        for i in range(len(self.resources)):
            compileState.pushStack(NamespaceType.UNROLLED_LOOP)
            compileState.currentNamespace()[varName] = self.resources[i]
            for child in block.children:
                compileState.compileFunction(child)
            compileState.popStack()

    def operation_get_element(self, compileState: CompileState, index: Resource) -> Resource:
        try:
            # noinspection PyTypeChecker
            index = int(index)
        except TypeError:
            raise McScriptTypeError(f"Expected a resource that can be converted to a number but got {repr(index)}",
                                    compileState)
        try:
            return self.resources[index]
        except IndexError:
            raise McScriptIndexError(index, compileState, len(self.resources) - 1)

    # no operation set_element because an array is a static construct and thus read-only
    def operation_set_element(self, compileState: CompileState, index: Resource, value: Resource):
        try:
            # noinspection PyTypeChecker
            index = int(index)
        except TypeError:
            raise McScriptTypeError(f"Expected a resource that can be converted to a number but got {index}",
                                    compileState)

        try:
            self.resources[index] = value
        except IndexError:
            raise McScriptIndexError(index, compileState, len(self.resources) - 1)

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        try:
            return self.attributes[name]
        except KeyError:
            raise McScriptAttributeError(f"Invalid attribute '{name}' of {self.type().value}", compileState)

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> ArrayResource:
        self.stack = stack
        new = []
        for index, resource in enumerate(self.resources[:]):
            if isinstance(resource, NullResource):
                new.append(resource)
            elif isinstance(resource, ValueResource) and resource.isStatic:
                new.append(resource)
            elif resource.storage == MinecraftDataStorage.SCOREBOARD:
                try:
                    new.append(resource.storeToNbt(self.stack[index], compileState))
                except TypeError:
                    raise McScriptTypeError(f"Array cannot store resource {resource.type().value}", compileState)
            else:
                new.append(resource)
        return ArrayResource(*new)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        return BooleanResource.TRUE if self.resources else BooleanResource.FALSE

    def toTextJson(self, compileState: CompileState, formatter: ResourceTextFormatter) -> List:
        resources: list = [self.resources[0]] if self.resources else []
        for resource in self.resources[1:]:
            resources.append(", ")
            resources.append(resource)
        return formatter.createFromResources("(", *resources, ")")

    def toNumber(self) -> int:
        raise NotImplementedError()

    def toString(self) -> str:
        raise NotImplementedError()

    def __str__(self):
        return f"Array({', '.join(str(i) for i in self.resources)})"

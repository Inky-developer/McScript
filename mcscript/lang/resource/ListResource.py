from __future__ import annotations

from typing import Callable, Dict, Optional, Type as TType, TYPE_CHECKING, Union, List

from lark import Tree

from mcscript.compiler.ContextType import ContextType
from mcscript.exceptions.compileExceptions import McScriptAttributeError, McScriptTypeError
from mcscript.lang.Type import Type
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.IntegerResource import IntegerResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.utility import isStatic
from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter

if TYPE_CHECKING:
    from mcscript.compiler.CompileState import CompileState


class ListResource(Resource):
    """
    The more dynamic version of an array.
    This Resource, unlike the array, stores it's data in an nbt list. This means that it cannot store constant values.
    This class defines methods to set an element at a given index and operations to insert completely new elements.

    Notes:
        the iterator copies the entire list to a temporary location. This can be really bad for performance if the list
        is huge or contains very complex objects. This also means that modifying the values in a for loop will not
        change the actual content of the list.

    See Also:
        :class:`mcscript.lang.resource.ArrayResource.ArrayResource`

        :class:`mcscript.lang.resource.base.ResourceBase.Resource`
    """

    def __init__(self, contentType: TypeResource, nbtAddress: NbtAddressResource = None):
        super().__init__()

        # use the second order classes since they should be the scoreboard classes
        # noinspection PyTypeChecker
        self.ContentResource: TType[VariableResource] = Resource.getResourceClass(contentType.value.type())

        if not issubclass(self.ContentResource, (ValueResource, VariableResource)):
            raise TypeError(f"Invalid type for Array: must be a value")

        self.nbtAddress: Optional[NbtAddressResource] = nbtAddress

        self.attributes: Dict[str, Callable[[CompileState], Resource]] = dict(
            size=self.getSize,
        )

        self.functions: Dict[str, InternalFunctionResource] = dict(
            append=self.AppendFunction(self),
            insert=self.InsertFunction(self)
        )

    def type(self) -> Type:
        return List

    def getSize(self, compileState: CompileState) -> IntegerResource:
        self._assertNbtAddress(compileState)

        stack = compileState.expressionStack.next()
        compileState.writeline(Command.LOAD_SCORE_NO_SCALE(
            stack=stack,
            var=self.nbtAddress,
        ))
        return IntegerResource(stack, False)

    def append(self, compileState: CompileState, value: Resource):
        if value.type() != self.ContentResource.type() or not isinstance(value, ValueResource):
            raise McScriptTypeError(f"Cannot append value of type {value.type().value} to list of type "
                                    f"{self.ContentResource.type().value}", compileState)
        self._assertNbtAddress(compileState)

        if value.isStatic:
            compileState.writeline(Command.APPEND_ARRAY(
                address=self.nbtAddress,
                value=value
            ))
        else:
            if not isinstance(value.value, NbtAddressResource):
                address = value.storeToNbt(NbtAddressResource(compileState.temporaryStorageStack.next().embed()),
                                           compileState)
                compileState.temporaryStorageStack.previous()
            else:
                address = value.value
            compileState.writeline(Command.APPEND_ARRAY_FROM(
                address=self.nbtAddress,
                address2=address
            ))

    def insert(self, compileState: CompileState, index: IntegerResource, value: Resource):
        if value.type() != self.ContentResource.type() or not isinstance(value, ValueResource):
            raise McScriptTypeError(f"Cannot insert value of type {value.type().value} to list of type "
                                    f"{self.ContentResource.type().value}", compileState)
        if not index.isStatic:
            raise McScriptTypeError(f"Index must be static. This could be implemented by appending to a new list",
                                    compileState)
        self._assertNbtAddress(compileState)

        if value.isStatic:
            compileState.writeline(Command.INSERT_ARRAY(
                address=self.nbtAddress,
                value=value,
                index=int(index)
            ))
        else:
            if not isinstance(value.value, NbtAddressResource):
                address = value.storeToNbt(NbtAddressResource(compileState.temporaryStorageStack.next().embed()),
                                           compileState)
                compileState.temporaryStorageStack.previous()
            else:
                address = value.value
            compileState.writeline(Command.INSERT_ARRAY_FROM(
                address=self.nbtAddress,
                address2=address,
                index=int(index)
            ))

    def get_iterator(self, compileState: CompileState, varName: str, tree: Tree):
        tempStack = NbtAddressResource(compileState.temporaryStorageStack.next().embed())
        tempArray = self.copy(tempStack, compileState)

        block = compileState.pushBlock(ContextType.LOOP, tree.line, tree.column)
        var = self.ContentResource(tempStack[0], False)
        compileState.currentContext().add_var(varName, var)

        # steps in the loop:
        # 1. set ´var´ equal to the current first value of the array
        # 2. run the user code
        # 3. remove the first value from the array
        # 4. if the array still has values, go to 1.
        for child in tree.children:
            compileState._compile_function(child)

        compileState.writeline(Command.REMOVE_VARIABLE(address=tempStack[0]))

        bool_stack = tempArray.getSize(compileState)
        compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=bool_stack,
                range="1.."
            ),
            command=Command.RUN_FUNCTION(function=block)
        ))

        compileState.popBlock()

        # only enter the loop if the array contains elements
        bool_stack = tempArray.getSize(compileState)
        compileState.writeline(Command.EXECUTE(
            sub=ExecuteCommand.IF_SCORE_RANGE(
                stack=bool_stack,
                range="1.."
            ),
            command=Command.RUN_FUNCTION(function=block)
        ))

    def operation_get_element(self, compileState: CompileState, index: Resource) -> Resource:
        if index.type() != ResourceType.INTEGER:
            raise McScriptTypeError(f"Expected type number as index but got {index.type().value}", compileState)
        if not isStatic(index):
            raise McScriptTypeError(f"Not yet implemented for non-static numbers! sorry :(", compileState)
        self._assertNbtAddress(compileState)
        return self.ContentResource(self.nbtAddress[index.toNumber()], False)

    def operation_set_element(self, compileState: CompileState, index: Resource, value: Resource):
        if not isinstance(index, IntegerResource):
            raise McScriptTypeError(f"Expected type number as index but got {index.type().value}", compileState)
        if not index.isStatic:
            raise McScriptTypeError(f"Not yet implemented for non-static numbers!", compileState)
        self._assertNbtAddress(compileState)
        if not isinstance(value, ValueResource):
            raise McScriptTypeError(f"For now, arrays can only store values", compileState)

        if value.isStatic:
            compileState.writeline(Command.SET_VARIABLE_VALUE(
                address=self.nbtAddress[int(index)],
                value=value
            ))
        else:
            value.storeToNbt(self.nbtAddress[int(index)], compileState)

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        try:
            return self.attributes[name](compileState)
        except KeyError:
            try:
                return self.functions[name]
            except KeyError:
                raise McScriptAttributeError(f"Invalid attribute '{name}' of {self.type().value}", compileState)

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> ListResource:
        self.nbtAddress = stack
        return self

    def copy(self, target: ValueResource, compileState: CompileState) -> ListResource:
        if not isinstance(target, NbtAddressResource):
            raise McScriptTypeError(f"Cannot copy a list to a location that is not in a data storage", compileState)
        self._assertNbtAddress(compileState)

        compileState.writeline(Command.COPY_VARIABLE(
            address=target,
            address2=self.nbtAddress
        ))
        return ListResource(TypeResource.fromType(self.ContentResource.type()), target)

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        """ True if the size of this is greater than zero"""
        return self.getSize(compileState).convertToBoolean(compileState)

    def toNumber(self) -> int:
        raise NotImplementedError()

    def toString(self) -> str:
        raise NotImplementedError()

    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Union[list, str]:
        if not self.nbtAddress:
            return "List()"
        return formatter.createFromResources(self.nbtAddress)

    def _assertNbtAddress(self, compileState: CompileState):
        if not self.nbtAddress:
            raise McScriptTypeError(f"cannot perform this operation because this resource was not yet stored on nbt",
                                    compileState)

    # Function classes
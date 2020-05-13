from __future__ import annotations

import re
from string import Formatter
from typing import Callable, Dict, List, Optional, TYPE_CHECKING, Tuple, Union

from lark import Tree

from mcscript.compiler.NamespaceType import NamespaceType
from mcscript.data.commands import Command, Struct
from mcscript.exceptions.compileExceptions import McScriptNotStaticError, McScriptTypeError
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.compiler.CompileState import CompileState
    from mcscript.compiler.Namespace import Namespace


class StringResource(ValueResource):
    """
    Holds a String.
    A string must always have a known length but its contents are allowed to change during runtime.
    These limitations are in place to allow efficient iteration over a string.
    A more mutable string class may be added later
    """

    class StringFormatter(Formatter):
        PATTERN = re.compile(r"\$(?:\((\w+)\)|(\w*))")

        def parse(self, format_string) -> Tuple[str, str, str, str]:
            lastMatch = 0
            for match in re.finditer(self.PATTERN, format_string):
                literal_text = format_string[lastMatch:match.span()[0]]
                name = match.group(1) or match.group(2)
                yield literal_text, name, "", None
                lastMatch = match.span()[1]
            yield format_string[lastMatch:], None, None, None

        def get_value(self, key, args, kwargs):
            if isinstance(key, int):
                if len(args) > key:
                    return args[key]
                # if not provided, return the dollar sign
                return "$"
            return kwargs[key]

    formatter = StringFormatter()

    def __init__(self, value: Union[str, NbtAddressResource], isStatic, length=None,
                 namespace: Optional[Namespace] = None):
        super().__init__(value, isStatic)

        self.attributes: Dict[str, Callable] = dict(length=self.getLength)
        self.length = len(value) if self.isStatic else length
        if self.length is None:
            raise ValueError(f"Non-static string must have a fixed and thus known length!")

        if namespace is not None:
            self.setValue(self.formatter.format(self.embed(), **namespace.asDict()), self.isStatic)

    @staticmethod
    def type():
        return ResourceType.STRING

    def embed(self) -> str:
        return self.value if self.isStatic else str(self.value)

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

    def getLength(self, _: CompileState) -> NumberResource:
        return NumberResource(self.length, True)

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        if attribute := self.attributes.get(name, None):
            return attribute(compileState)

    def allow_redefine(self, compileState) -> bool:
        return compileState.currentNamespace().isContextStatic()

    def operation_get_element(self, compileState: CompileState, index: Resource) -> Resource:
        number = index.convertToNumber(compileState)
        if not number.isStatic:
            raise McScriptTypeError("Index access for string must be static", compileState)
        if self.isStatic:
            return StringResource(self.value[number.toNumber()], True)

        return StringResource(self.value[number.toNumber()], False, length=1)

    def operation_set_element(self, compileState: CompileState, index: Resource, value: Resource):
        number = index.convertToNumber(compileState)

        if not number.isStatic:
            raise McScriptTypeError(f"The index must be a static value", compileState)

        number = number.toNumber()
        # negative numbers can lead to bugs
        if number < 0:
            number = self.length - number - 2

        if not isinstance(value, StringResource):
            raise McScriptTypeError(f"Expected type String but got {value.type().value}", compileState)

        if value.length != 1:
            raise McScriptTypeError(f"Expected single character but string had length {value.length}", compileState)

        if self.isStatic:
            if not value.isStatic:
                raise McScriptTypeError(f"Cannot set non-static string as character for static string {self.value}. "
                                        f"Consider using a static string as value.", compileState)
            else:
                self.value = self.value[:number] + value.toString() + self.value[number + 1:]
        else:
            if value.isStatic:
                compileState.writeline(Command.SET_VARIABLE_VALUE(
                    address=self.value[number],
                    value=f'"{value}"'
                ))
            else:
                compileState.writeline(Command.COPY_VARIABLE(
                    address=self.value[number],
                    address2=value.value[0]
                ))

    def operation_plus(self, other: ValueResource, compileState: CompileState) -> ValueResource:
        if not isinstance(other, StringResource):
            raise McScriptTypeError(f"Can only concatenate strings, not {other.type().value}", compileState)

        if self.isStatic and other.isStatic:
            return StringResource(self.value + other.value, True)

        # if self.isStatic:
        #     raise McScriptIsStaticError(
        #         f"Can not concatenate static string ({self.value}) with non-static string!", compileState
        #     )

        if not compileState.currentNamespace().isContextStatic():
            raise McScriptNotStaticError("This operation can only be performed in a static context!", compileState)

        resource = StringResource(
            NbtAddressResource(compileState.temporaryStorageStack.next().embed()),
            False,
            self.length + other.length
        )
        compileState.writeline(Command.COPY_VARIABLE(
            address=resource.value,
            address2=self.value
        ))
        if other.isStatic:
            for char in other.value:
                compileState.writeline(Command.APPEND_ARRAY(
                    address=resource.value,
                    value=f'"{char}"'
                ))
        else:
            for i in range(other.length):
                compileState.writeline(Command.APPEND_ARRAY_FROM(
                    address=resource.value,
                    address2=other.value[i]
                ))

        return resource

    def iterate(self, compileState: CompileState, varName: str, block: Tree):
        for i in range(self.length):
            compileState.pushStack(NamespaceType.LOOP)
            compileState.currentNamespace()[varName] = self.operation_get_element(compileState, NumberResource(i, True))
            for child in block.children:
                compileState.compileFunction(child)
            compileState.popStack()

    def convertToBoolean(self, compileState: CompileState) -> BooleanResource:
        if self.isStatic:
            return BooleanResource.TRUE if self.value else BooleanResource.FALSE
        return self.getLength(compileState).convertToBoolean(compileState)

    def storeToNbt(self, stack: NbtAddressResource, compileState: CompileState) -> Resource:
        if not self.isStatic:
            if stack == self.value:
                return self
            compileState.writeline(Command.COPY_VARIABLE(
                address=stack,
                address2=self.value
            ))
            return StringResource(
                stack,
                False,
                self.length
            )
        compileState.writeline(Command.SET_VARIABLE(
            address=stack.address,
            struct=Struct.VAR(var=stack.name, value=Struct.ARRAY(
                f'"{i}"' for i in self.value
            ))
        ))
        return StringResource(stack, False, len(self.value))

    def load(self, compileState: CompileState, stack: ValueResource = None) -> Resource:
        return self

    def toTextJson(self, compileState: CompileState, formatter: ResourceTextFormatter) -> List:
        if self.isStatic:
            raise TypeError
        return formatter.createFromResources(*[NbtAddressResource(self.value[i].embed()) for i in range(self.length)])

    def format(self, *args, **kwargs) -> StringResource:
        r"""
        Stringformat. used to insert variables into the string
        each '$' symbol gets replaced by an argument; the first $ will be replaced by the first argument and so on.
        all occurrences of '$(name)' will be replaced with the name value in kwargs.
        all arguments must be used.
        To escape a '$' symbol, use '\$'
        :param args: the arguments for the replacement
        :param kwargs: named arguments
        :return: a string resource with the replaced content
        """
        if not self.isStatic:
            raise TypeError("Can not stringformat a non-static string!")

        return StringResource(self.formatter.format(self.embed(), *args, **kwargs), True)

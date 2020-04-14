from __future__ import annotations

import re
from string import Formatter
from typing import Callable, Dict, Optional, TYPE_CHECKING, Tuple, Union

from lark import Tree

from mcscript import Logger
from mcscript.Exceptions.compileExceptions import McScriptTypeError
from mcscript.compiler.Namespace import Namespace
from mcscript.compiler.NamespaceType import NamespaceType
from mcscript.data.commands import Command, Struct
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType

if TYPE_CHECKING:
    from mcscript.lang.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.compiler.CompileState import CompileState


class StringResource(ValueResource):
    """
    Holds a String
    """

    class StringFormatter(Formatter):
        PATTERN = re.compile(r"\$(\w*)")

        def parse(self, format_string) -> Tuple[str, str, str, str]:
            lastMatch = 0
            for match in re.finditer(self.PATTERN, format_string):
                literal_text = format_string[lastMatch:match.span()[0]]
                name = match.group(1)
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
        return self.value if self.isStatic else self.value.embed()

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

    def getLength(self, _: CompileState) -> NumberResource:
        return NumberResource(self.length, True)

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        if attribute := self.attributes.get(name, None):
            return attribute(compileState)

    def operation_get_element(self, compileState: CompileState, index: Resource) -> Resource:
        number = index.convertToNumber(compileState)
        if not number.isStatic:
            raise McScriptTypeError("Index access for string must be static", compileState)
        if self.isStatic:
            return StringResource(self.value[number], True)

        return StringResource(self.value[number.toNumber()], False, length=1)

    def operation_set_element(self, compileState: CompileState, index: Resource, value: Resource):
        number = index.convertToNumber(compileState)

        if not number.isStatic:
            raise McScriptTypeError(f"Index must be a static value, because I did not implement it yet.", compileState)

        number = number.toNumber()

        if not isinstance(value, StringResource):
            raise McScriptTypeError(f"Expected type String but got {value.type().value}", compileState)

        if value.length > 1:
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
        # ToDo: a + 1 will modify the memory of a but not it's size which will lead to strange behavior
        if not isinstance(other, StringResource):
            if not other.isStatic:
                Logger.error(f"[StringResource] other is neither a string nor static!")
                return NotImplemented
            other = StringResource(str(other), True)

        if self.isStatic:
            return StringResource(self.value + other.value, True)

        if other.isStatic:
            for char in other.value:
                compileState.writeline(Command.APPEND_ARRAY(
                    address=self.value,
                    value=f'"{char}"'
                ))
        else:
            for i in range(other.length):
                compileState.writeline(Command.APPEND_ARRAY_FROM(
                    address=self.value,
                    address2=other.value[i]
                ))
        return StringResource(self.value, False, self.length + other.length)

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
            return self
        compileState.writeline(Command.SET_VARIABLE(
            address=stack.address,
            struct=Struct.VAR(var=stack.name, value=Struct.ARRAY(f'"{i}"' for i in self.value))
        ))
        return StringResource(stack, False, len(self.value))

    def load(self, compileState: CompileState, stack: ValueResource = None) -> Resource:
        return self

    def toJsonString(self, compileState: CompileState, formatter: ResourceTextFormatter) -> str:
        if self.isStatic or self.length == 1:
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

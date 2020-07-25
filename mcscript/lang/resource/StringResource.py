from __future__ import annotations

import re
from string import Formatter
from typing import Callable, Dict, Optional, Tuple, TYPE_CHECKING, Union

from lark import Tree

from mcscript.compiler.ContextType import ContextType
from mcscript.exceptions.compileExceptions import McScriptTypeError
from mcscript.lang.resource.BooleanResource import BooleanResource
from mcscript.lang.resource.NbtAddressResource import NbtAddressResource
from mcscript.lang.resource.NumberResource import NumberResource
from mcscript.lang.resource.base.ResourceBase import Resource, ValueResource
from mcscript.lang.resource.base.ResourceType import ResourceType
from mcscript.utils.JsonTextFormat.objectFormatter import format_text

if TYPE_CHECKING:
    from mcscript.compiler.Context import Context
    from mcscript.utils.JsonTextFormat.ResourceTextFormatter import ResourceTextFormatter
    from mcscript.compiler.CompileState import CompileState


class StringResource(Resource):
    """
    Holds a String.

    Things the compiler can know about a string:
        * Literal value: string is statically known. Every method expect working with non-static strings supported

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

    def __init__(self, value: str,
                 context: Optional[Context] = None):
        super().__init__()

        self.static_value = value
        self.length = len(value) 

        self.attributes: Dict[str, Callable] = dict(length=self.getLength)

        if context is not None:
            namespace_dict = context.as_dict()
            replacements = {
                key: namespace_dict[key].resource for key in namespace_dict}
            self.static_value = self.formatter.format(self.static_value, **replacements)

    @staticmethod
    def type():
        return ResourceType.STRING

    def getLength(self, compileState: CompileState) -> NumberResource:
        if self.length is not None:
            return NumberResource(self.length, True)

        raise ValueError("Length of string unknown")

    def getAttribute(self, compileState: CompileState, name: str) -> Resource:
        if attribute := self.attributes.get(name, None):
            return attribute(compileState)

    def operation_get_element(self, compileState: CompileState, index: Resource) -> Resource:
        try:
            number = index.integer_value()
        except TypeError:
            raise McScriptTypeError(f"Expected a number, but got type {index.type().value}", compileState)

        return StringResource(self.value[number.toNumber()])

    def operation_set_element(self, compileState: CompileState, index: Resource, value: Resource):
        """
        Replaces a character in this string by another character.
        ToDo: add bound and size checking runtime errors for debug builds
        ToDo: check if the operation is valid in the current context

        Combinations:
            - static - static: Ok
            - static - non static: Error - cannot replace a character of a static string by a non-static string
            - non static - static: Ok (Note: no bounds checking)
            - non static - non static: Ok (Note no bounds checking, no size checking)

        Args:
            compileState: the compile state
            index: the static access index
            value: the one-character string to replace a character of this string

        Returns:
            None. The operation modifies this existing string
        """
        try:
            number = index.integer_value()
        except TypeError:
            raise McScriptTypeError(f"Expected a number, but got type {index.type().value}", compileState)

        try:
            new_value = value.string_value()
        except TypeError:
            raise McScriptTypeError(f"Expected a character, but got type {index.type().value}", compileState)

        if len(new_value) != 1:
            raise McScriptTypeError(f"Expected a single character, got {len(new_value)}", compileState)

        self.static_value[number] = new_value

    def operation_plus(self, other: StringResource, compileState: CompileState) -> ValueResource:
        """
        Concatenates this string with the other string.
        ToDo: check if the operation is valid in the current context

        Combinations:
            - static - static: Ok
            - static - non static: Err
            - non static - static: Ok
            - non static - non static: Ok

        Args:
            other: the other string
            compileState: the compile state

        Returns:
            The concatenated string
        """
        if not isinstance(other, StringResource):
            raise McScriptTypeError(
                f"Can only concatenate strings, not {other.type().value}", compileState)

        return StringResource(self.static_value + other.static_value)

    def iterate(self, compileState: CompileState, varName: str, block: Tree):
        if self.length is None:
            raise McScriptTypeError(f"Cannot iterate over a string with unknown length (ToDo implement that)",
                                    compileState)

        for i in range(self.length):
            with compileState.node_block(ContextType.UNROLLED_LOOP, block.line, block.column):
                context.add_var(
                    varName,
                    self.operation_get_element(
                        compileState, NumberResource(i, True))
                )
                for child in block.children:
                    compileState.compileFunction(child)

    def toTextJson(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Dict:
        return format_text(self.static_value)

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

from __future__ import annotations

import re
from string import Formatter
from typing import Tuple, TYPE_CHECKING, Optional

from src.mcscript.compiler import Namespace
from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType

if TYPE_CHECKING:
    pass


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

    def __init__(self, value, isStatic, namespace: Optional[Namespace] = None):
        super().__init__(value, isStatic)

        if namespace is not None:
            self.setValue(self.formatter.format(self.embed(), **namespace.asDict()), self.isStatic)

    @staticmethod
    def type():
        return ResourceType.STRING

    def embed(self) -> str:
        return self.value

    def typeCheck(self) -> bool:
        return isinstance(self.value, str)

    def format(self, *args, **kwargs) -> StringResource:
        """
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
            raise TypeError

        return StringResource(self.formatter.format(self.embed(), *args, **kwargs), True)

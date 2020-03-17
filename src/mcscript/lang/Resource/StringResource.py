from __future__ import annotations

from string import Formatter
from typing import Tuple, List

from src.mcscript.lang.Resource.ResourceBase import ValueResource
from src.mcscript.lang.Resource.ResourceType import ResourceType


class StringResource(ValueResource):
    """
    Holds a String
    """

    class StringFormatter(Formatter):
        def parse(self, format_string) -> Tuple[str, str, str, str]:
            literal_text: List[str] = []
            field: List[str] = []
            lastIsField = False
            inField = False
            for character in format_string:
                if inField:
                    if character != ")":
                        field.append(character)
                    else:
                        inField = False
                        lastIsField = False
                        yield "".join(literal_text), "".join(field), "", None
                        literal_text = []
                        field = []
                elif lastIsField and character == "(":
                    inField = True
                elif lastIsField:
                    lastIsField = False
                    yield "".join(literal_text), "", "", None
                    literal_text = [character]
                elif character == "$":
                    lastIsField = True
                else:
                    literal_text.append(character)

            if literal_text:
                _field = "".join(field) if lastIsField else None
                yield "".join(literal_text), _field, "", None
            return

    formatter = StringFormatter()

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

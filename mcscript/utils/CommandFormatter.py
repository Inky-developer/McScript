from enum import Enum
from string import Formatter
from typing import Dict, Any


class CommandFormatter(Formatter):
    """
    Advanced format mini-language.

    Features:
        - numeric placeholders and empty placeholders get replaced with empty strings
        - placeholder names that are not specified don't throw an error and instead write an empty string
        - if a placeholder name is not specified it can write a default value which is specified after a colon:
            - if it does not contain a dot it is the literal default value
            - if it does contain a dot a value of one of the in commands defined enums will be used

    Examples:
        ``format("Text") -> Text``

        ``format("{greeting:hello}, {}{world}, world="world")!" -> "hello, world!"``

        ``format("{greeting:hello}, {}{world}, greeting="servus", world="world")!" -> "servus, world!"``

        ``format("property: {:Config.currentConfig.NAME}") -> <depending on config>"property: McScript"``
    """
    DEFAULT_STRING = ""

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def get_field(self, field_name: str, args, kwargs):
        if field_name.isnumeric():
            return "", None
        if field_name in kwargs:
            return kwargs[field_name], field_name
        return "", None

    def format_field(self, value, format_spec):
        if not value and format_spec:
            if "." not in format_spec:
                return format_spec
            else:
                enumName, *properties = format_spec.split(".")
                enum = self.context[enumName]
                for member in properties:
                    enum = getattr(enum, member)
                return str(enum.value if isinstance(enum, Enum) else enum)
        return str(value)

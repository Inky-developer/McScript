from enum import Enum
from string import Formatter
from typing import Dict, Any


class CommandFormatter(Formatter):
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

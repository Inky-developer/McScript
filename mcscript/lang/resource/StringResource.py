from __future__ import annotations

import re
from string import Formatter
from typing import Dict, Optional, Tuple, TYPE_CHECKING

from mcscript.lang.Type import Type
from mcscript.lang.atomic_types import String
from mcscript.lang.resource.base.ResourceBase import Resource
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

        if context is not None:
            namespace_dict = context.as_dict()
            replacements = {
                key: namespace_dict[key].resource for key in namespace_dict}
            self.static_value = self.formatter.format(self.static_value, **replacements)

    def type(self) -> Type:
        return String

    def to_json_text(self, compileState: CompileState, formatter: ResourceTextFormatter) -> Dict:
        return format_text(self.static_value)

    def supports_scoreboard(self) -> bool:
        return False

    # Todo return True
    def supports_storage(self) -> bool:
        return False

    def __str__(self):
        return self.static_value

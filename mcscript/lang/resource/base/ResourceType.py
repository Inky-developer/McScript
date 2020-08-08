from __future__ import annotations

from enum import Enum


class ResourceType(Enum):
    """
    A list of all resource types.
    The values are the names that can be used in mcscript.
    """
    NULL = "Null"
    STRUCT = "Struct"
    STRUCT_OBJECT = "Object"
    INTEGER = "Int"
    FIXED_POINT = "Fixed"
    BOOLEAN = "Boolean"
    STRING = "String"
    SELECTOR = "Selector"
    ENUM = "Enum"
    TYPE = "Type"
    FUNCTION = "Function"
    MACRO = "Macro"

    TUPLE = "Tuple"
    LIST = "List"

    ANY = "Any"
    NUMBER = "Number"

    def is_subtype(self, other: ResourceType) -> bool:
        """
        Returns whether the other type is the same type or a subtype

        Args:
            other: the other type

        Returns:
            whether the other type is a subtype or the same type
        """
        return self == other or other == ResourceType.ANY or (
                other == ResourceType.NUMBER and self in (ResourceType.INTEGER, ResourceType.FIXED_POINT)
        )

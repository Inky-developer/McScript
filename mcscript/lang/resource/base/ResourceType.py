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

    TUPLE = "Tuple"
    LIST = "List"


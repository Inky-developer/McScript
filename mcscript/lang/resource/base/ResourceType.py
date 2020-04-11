from enum import Enum, auto


class ResourceType(Enum):
    """
    A list of all resource types.
    The values are the names that can be used in mcscript.
    """
    NULL = "Null"
    ADDRESS = auto()
    NBT_ADDRESS = auto()
    STRUCT = auto()
    STRUCT_OBJECT = auto()
    NUMBER = "Number"
    FIXED_POINT = "Fixed"
    BOOLEAN = "Boolean"
    STRING = "String"
    SELECTOR = "Selector"
    ENUM = "Enum"
    FUNCTION = "Function"
    METHOD = "Method"
    TYPE = auto()

    RESOURCE = "Resource"
    VALUE_RESOURCE = "ValueResource"